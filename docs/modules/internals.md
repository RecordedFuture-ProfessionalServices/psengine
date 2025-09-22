## Decorators

Within PSEngine we use a series of decorators to make the developer’s life easier. Some are built in `psengine.helpers`, others come from different libraries.
We use these decorators on user-facing (public) methods only, unless in rare circumstances.

#### `validate_call` decorator

This decorator (implemented by `pydantic`) validates the method’s parameters and output with the type hints supplied and raises a `ValidationError` if something is called with the wrong type. This means there is no longer a necessity to check the instance type of parameters in the code. For example, the below code is not needed anymore and can be shortened with this decorator:

```python
def my_func(x: int) -> int:
    if isinstance(x, int):
        return x
    else:
        raise ValueError('x is not an int')
```

Rewritten with the `validate_call` decorator:

```python
from pydantic import validate_call

@validate_call
def my_func(x: int) -> int:
    return x
```

#### `debug_call` decorator

This decorator logs the input and output of a method at debug level. It is built in to `psengine`.

#### `connection_exceptions` decorator

This decorator is built in to `psengine` and handles HTTP-related exceptions.
It helps you avoid having to remember all the HTTP exceptions that a request can raise.

Apply it to a method and specify the custom exception to raise instead.

For example, here we raise a `NewFeatureLookupError` for any request that does not return HTTP 2xx or 404.
In case of a 200 the response is returned; in case of a 404, `None` is returned.

```python
from pydantic import validate_call

from .exceptions import NewFeatureLookupError
from .new_feature import NewFeature

from ..helpers import debug_call, connection_exceptions
from ..rf_client import RFClient
from ..endpoints import EP_NEW_FEATURE_LOOKUP

class NewFeatureMgr:
    # ... your init and code here ...

    @debug_call
    @validate_call
    @connection_exception(ignore_status_code=[404], exception_to_raise=NewFeatureLookupError)
    def lookup(id: str) -> NewFeature:
        response = self.rf_client.request('get', EP_NEW_FEATURE_LOOKUP + id).json()
        return NewFeature.enhanced_model_validate(response)
```

`total_ordering`
This decorator comes from the `functools` module in the standard library. It dynamically defines the ordering operations given at least two predefined ones. You only need to define `__eq__` and `__gt__` methods in a class and the decorator implements the others.

We use this decorator on top of ADTs (see more on this below) when it makes sense, based on attributes suitable for ordering.

## Pydantic

With `pydantic` we create models representing the data coming from the API. This lets us know that once we get the data back, we are sure they are of the type we expect, avoiding the need for most validation in your code. For example, if we get the risk score of an IOC back, it is validated as `int`; we don’t have to check if the risk score is an integer in the code.

A model looks like this:

```python
from typing import Optional

from ..common_models import RFBaseModel


class RiskScore(RFBaseModel):
    risk_score: Optional[int] = None
    risk_rule: Optional[str] = None
    ioc: str
```

Here we say that `risk_score` and `risk_rule` are `Optional`, meaning they might not be present in the payload, but if they are present they have to be strings. The default value is `None` but it is not what is assigned to the parameter. The only required parameter is `ioc`, which represents a string.

We use `RFBaseModel`, which is a `pydantic.BaseModel` with a few additional settings. Each model should inherit from it. Models can have other models as validators. For example, below the `risk_rule` parameter is a list of `RiskRule` models.

```python
from typing import Optional, List

from ..common_models import RFBaseModel


class RiskRule(RFBaseModel):
    name: str
    type_: str


class RiskScore(RFBaseModel):
    risk_score: Optional[int] = None
    risk_rule: List[RiskRule]
    ioc: str
```

Some fields in the Recorded Future API use JSON naming conventions, for example `IpAddress`. Since `pydantic` needs field names mapped correctly to the incoming payload for validation, to validate the JSON below:

```json
{
  "a": 1,
  "b": 2
}
```

We need a `pydantic` model with `a` and `b` as fields:

```python
class MyModel(BaseModel):
    a: int
    b: int
```

However, Python naming conventions for variables and parameters differ from JSON. A field like `IpAddress` in Python would be `ip_address`; hence `pydantic` allows the use of an `alias`:

```python
from pydantic import Field

from ..common_models import RFBaseModel


class IPAddress(RFBaseModel):
    ip_address: str = Field(alias='IpAddress', default=None)
```

Sometimes the Recorded Future API has constraints that cannot be easily expressed via `pydantic`. For example, in the Detection Rule API if the detection type is `detection_rule` we must have the `id` and `sub_type` fields. This can be defined with a `@model_validator` decorator of `pydantic`. It allows you to define a function to execute before or after (based on the `mode`) the `pydantic` validation.

## ADT

ADT (Abstract Data Type) models are used by the manager class and the end user. The difference between an ADT and a `pydantic` model is that, even though an ADT is a `pydantic` model, it has additional features, for example special methods (`__str__`, `__eq__`, etc.) and properties.

A `pydantic` model used by the user represents the payload sent to or returned by an API endpoint. For example, a POST endpoint can receive a `pydantic` model as input and return a `pydantic` model as output. As such, those models have a suffix of `In` or `Out` based on the direction (In to the API, Out of the API).

### Naming Convention

We use a naming convention for classes:

- Manager is called `<ADT>Mgr`.
- The ADT is named after the object it represents. For example, the ADT of an Analyst Note is `AnalystNote`.
- `pydantic` models used by users that are not ADTs are suffixed with `In` or `Out`. For example, the `Preview` payload to be sent to the `/analystnote/preview` endpoint can be called `AnalystNotePreviewIn`.
