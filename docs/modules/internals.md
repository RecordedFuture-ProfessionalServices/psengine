## Decorators

Within PSEngine we use a series of decorators to make the developer’s life easier. Some are built in `psengine.helpers`, others comes for different libraries.
We use this decorators on user facing (public) methods only unless some rare circumstances.

#### `validate_call` decorator

This decorator (implemented by `pydantic`) will validate the method’s parameters and output with the type hinting supplied and will raise a `ValidationError` if something is called with the wrong type. This means there is no more the necessity to check the instance type of the parameters in the code.  For example, the below code is not needed anymore, and can be shortened with this decorator:

```python
def my_func(x: int) -> int:
  if isinsance(x, int) -> int:
    return x
  else 
    raise ValueError('x is not an int')
```
Rewrote with the `validate_call` decorator it is:

```python
from pydantic import validate_call
@validate_call
def my_func(x: int) -> int:
  return x
```

#### `debug_call` decorator

This decorator will log in debug the input and output of a method. It is built-in in `psengine`.

#### `connection_exceptions` decorator

This decorator is builint in `psengine` and will handle the HTTP related exceptions. 
It is useful to avoid having to remember all the HTTP exceptions that a request can raise. 

The way to use it is to apply it to a method and specify the custom exception to be raised instead. 

For example, here we are going to raise a `NewFeatureLookupError` for any request that does not return HTTP 2xx or 404. 
In case of a 200 the response will be returned, in case of a 404, `None` will be returned. 

```python
from pydantic import validate_call

from .exceptions import NewFeatureLookupError
from .new_feature import NewFeature

from ..helpers import debug_call, connection_exceptions
from ..rf_client import RFClient
from ..endpoints import EP_NEW_FEATURE_LOOKUP

class NewFeatureMgr:
  #... your init and code here ...

  @debug_call
  @validate_call
  @connection_exception(ignore_status_code=[404], exception_to_raise=NewFeatureLookupError)
  def lookup(id: str) -> NewFeature:
      response = self.rf_client.request('get', EP_NEW_FEATURE_LOOKUP + id).json()
      return NewFeature.enhanced_model_validate(response) 
```

`total_ordering`
This decorator comes from the `functools` module in the standard library. It is used to dynamically define the ordering operations given at least two predefined ones. We only need to define `__eq__` and `__gt__`  methods in a class and the decorator will implement the others. 

We use this decorator on top of ADTs (see more on this below), when it make sense based on attributes that makes sense for ordering. i

## Pydantic

With `pydantic` we create models for representing the data coming from the API. This allows us to know that once we got the data back, we are sure that they are of the type we expect, avoiding the developer to do most of the validation. For example if we get the risk score of an IOC back, it is validated as `int`, we don’t have to check if the risk score is an integer in the code. 

A model look like this: 


```python
from typing import Optional

from ..common_models import RFBaseModel


class RiskScore(RFBaseModel):
    risk_score : Optional[int] = None
    risk_rule : Optional[str] = None
    ioc : str
```

Here we are saying that the `risk_score` and `risk_rule` are `Optional`, meaning they might not be present in the payload, but if they are present they have to be strings. The default value is `None` but it is not what is assigned to the parameter. The only required parameter is `ioc` which represent a string. 

We use `RFBaseModel` which is a `pydantic.BaseModel` with a few additional settings. Each model should inherit from it. Models can have other models as validators. For example below the `risk_rule` parameter is a list of `RiskRule` models.

```python
from typing import Optional, List

from ..common_models import RFBaseModel


class RiskRule(RFBaseModel):
  name: str
  type_: str


class RiskScore(RFBaseModel):
    risk_score : Optional[int] = None
    risk_rule : List[RiskRule]
    ioc : str
```

Some fields in the Recorded Future API are using the JSON naming convention, for example `IpAddress`. Since `pydantic` to work has to have the names mapped correctly based on what it is received for validation. For example, to validate the below json:

```json
{
  "a" : 1, 
  "b" : 2
}
```

We need a `pydantic` model that has `a` and `b` as fields. 

```python
class MyModel(BaseModel):
  a: int
  b: int
```

However, Python naming convention of variables and parameters is different from JSON. A field like `IpAddress` in python would be called `ip_address` hence `pydantic` allows us to use the `alias`

```python
from pytantic import Field

from ..common_models import RFBaseModel


class IPAddress(RFBaseModel):
  ip_address: str = Field(alias='IpAddress', default=None)

```

Sometimes the Recorded Future API has some constraints that cannot be easily expressed via `pydantic`. For example in the Detection Rule API if the detection type is `detection_rule` we must have the `id` and `sub_type` fields. This can be defined with a `@model_validator` decorator of `pydantic`. It basically allows you to define a function to execute before or after (based on the `mode`) the `pydantic` validation has happened. 

## ADT

ADT (Abstract Data Type) are models used by the manager class AND the end user. The difference between an ADT and a `pydantic` Model is that, even though an ADT is a `pydantic` model, it has some additional features, for example: special methods (`__str__`, `__eq__` etc) and properties. 

A `pydantic` model used by the user is a model representing the payload sent to or returned by an API endpoint. For example a POST endpoint can receive a `pydantic` model as input and return a `pydantic` model as output. As such those models have a suffix of `In` or `Out` based on the direction (In the API, Out of the API). 

### Naming Convention

We use a naming convention for classes: 

Manager is called `<ADT>Mgr`

The ADT is called after the object it represents. For example the ADT of an Analyst Note is called `AnalystNote`.

Pydantic models used by users that are not ADT are suffixed with `In` or `Out`. For example specifying the `Preview` payload to be sent to the `/analystnote/preview` endpoint can be called `AnalystNotePreviewIn`.
