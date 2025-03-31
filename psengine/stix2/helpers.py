##################################### TERMS OF USE ###########################################
# The following code is provided for demonstration purpose only, and should not be used      #
# without independent verification. Recorded Future makes no representations or warranties,  #
# express, implied, statutory, or otherwise, regarding any aspect of this code or of the     #
# information it may retrieve, and provides it both strictly “as-is” and without assuming    #
# responsibility for any information it may retrieve. Recorded Future shall not be liable    #
# for, and you assume all risk of using, the foregoing. By using this code, Customer         #
# represents that it is solely responsible for having all necessary licenses, permissions,   #
# rights, and/or consents to connect to third party APIs, and that it is solely responsible  #
# for having all necessary licenses, permissions, rights, and/or consents to any data        #
# accessed from any third party API.                                                         #
##############################################################################################

from .complex_entity import IndicatorEntity
from .constants import CONVERT_ENTITY_KWARGS, INDICATOR_TYPES
from .errors import STIX2TransformError, UnsupportedConversionTypeError
from .simple_entity import TTP, Identity, Malware, Vulnerability

SIMPLE_ENTITY_MAP = {
    'MitreAttackIdentifier': TTP,
    'Company': Identity,
    'Person': Identity,
    'Organization': Identity,
    'Malware': Malware,
    'CyberVulnerability': Vulnerability,
}


def convert_entity(
    name: str,
    entity_type: str,
    create_indicator: bool = True,
    create_obs: bool = False,
    **kwargs,
):
    """Converts RF entity to STIX2.

    Args:
        name (str): Name of entity
        entity_type (str): Recorded Future type of entity
        create_indicator (bool, optional): flag to determine if create indicator
        create_obs (bool, optional): flag to determine if create observable
        **kwargs: Any other fields that can be used in an entity.
                  Must be one of CONVERT_ENTITY_KWARGS

    No Longer Returned:
        A subclass of RFBaseEntity.
    """
    for key in kwargs:
        if key not in CONVERT_ENTITY_KWARGS:
            msg = f'{key} is invalid keyword argument for convert_entity. Only {CONVERT_ENTITY_KWARGS} are accepted'  # noqa: E501
            raise STIX2TransformError(msg)
    if entity_type in INDICATOR_TYPES:
        return IndicatorEntity(
            name=name,
            type_=entity_type,
            create_indicator=create_indicator,
            create_obs=create_obs,
        )
    elif entity_type in SIMPLE_ENTITY_MAP:
        ent = SIMPLE_ENTITY_MAP[entity_type]
        if ent == Identity:
            return ent(name, rf_type=entity_type)
        return SIMPLE_ENTITY_MAP[entity_type](name, **kwargs)
    else:
        raise UnsupportedConversionTypeError(
            f'Could not convert entity {name} because type {entity_type} is not supported',
        )
