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
# accessed from any third party API.                                                         #.
##############################################################################################

import uuid

import stix2
from stix2.canonicalization.Canonicalize import canonicalize

from .constants import RF_IDENTITY_UUID, RF_NAMESPACE


def generate_uuid(**kwargs: dict) -> str:
    """Generated a unique UUID to be used as a STIX2 ID.

    Args:
        **kwargs (dict): a list of parameters to be hashed for the UUId.
            Usually just {name:'somename'}, but could be more complex
    """
    data = {k: str(v) for k, v in kwargs.items()}
    data = canonicalize(data, utf8=False)
    return str(uuid.uuid5(uuid.UUID(RF_NAMESPACE), data))


def create_rf_author() -> stix2.v21.Identity:
    """Create the Recorded Future Author Identity.

    Returns:
        stix2.v21.Identity: Recorded Future, as an identity
    """
    name = 'Recorded Future'
    id_class = 'organization'
    return stix2.Identity(
        name=name,
        identity_class=id_class,
        id=RF_IDENTITY_UUID,
        description=(
            'Recorded Future is the most comprehensive and independent threat'
            ' intelligence cloud platform. We enable organizations to identify and mitigate'
            ' threats across cyber, supply-chain, physical and fraud domains; and are trusted'
            ' to get real-time, unbiased and actionable intelligence.'
        ),
        contact_information='support@recordedfuture.com',
    )
