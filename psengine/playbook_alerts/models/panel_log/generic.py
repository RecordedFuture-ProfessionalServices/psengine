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

from ....common_models import IdOptionalNameType
from .common import Assignee, ChangeType


class PriorityChange(ChangeType):
    old: str
    new: str


class StatusChange(ChangeType):
    old: str
    new: str
    actions_taken: list


class OldNewOptionalType(ChangeType):
    """This is valid for the following Panel Log types.

    - `ExternalIdChange`,
    - `DescriptionChange`,
    - `TitleChange`,
    - `ReopenStrategyChange`

    """

    old: str | None = None
    new: str | None = None


class AddedRemovedTypeEntities(ChangeType):
    """This is valid for the following Panel Log types.

    - `EntityChangeV2`,
    - `RelatedEntityChangeV2`
    """

    removed: list[IdOptionalNameType] | None = []
    added: list[IdOptionalNameType] | None = []


class AddedRemovedList(ChangeType):
    removed: list[str] | None = []
    added: list[str] | None = []


class CommentChange(ChangeType):
    comment: str


class AssigneeChange(ChangeType):
    old: Assignee | None = None
    new: Assignee | None = None


class OnwardActionsRemovedChange(ChangeType):
    removed_actions_taken: list[str] | None = []


class OnwardActionsAddedChange(ChangeType):
    added_actions_taken: list[str] | None = []
