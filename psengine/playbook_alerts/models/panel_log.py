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

from datetime import datetime
from typing import Optional

from pydantic import Field, HttpUrl, model_validator

from ...common_models import IdOptionalNameType, RFBaseModel


class ChangeType(RFBaseModel):
    type_: str = Field(alias='type')


class PriorityChange(ChangeType):
    old: str
    new: str


class StatusChange(ChangeType):
    old: str
    new: str
    actions_taken: list


class OldNewOptionalType(ChangeType):
    """This is valid for the following Panel Log types.

    - ``ExternalIdChange``,
    - ``DescriptionChange``,
    - ``TitleChange``,
    - ``ReopenStrategyChange``

    """

    old: Optional[str] = None
    new: Optional[str] = None


class AddedRemovedTypeEntities(ChangeType):
    """This is valid for the following Panel Log types.

    - ``EntityChangeV2``,
    - ``RelatedEntityChangeV2``
    """

    removed: Optional[list[IdOptionalNameType]] = []
    added: Optional[list[IdOptionalNameType]] = []


class AddedRemovedList(ChangeType):
    removed: Optional[list[str]] = []
    added: Optional[list[str]] = []


class CommentChange(ChangeType):
    comment: str


class Assignee(RFBaseModel):
    id_: str = Field(alias='id')
    name: str


class AssigneeChange(ChangeType):
    old: Optional[Assignee] = None
    new: Optional[Assignee] = None


class DnsRecord(RFBaseModel):
    type_: Optional[str] = Field(alias='type', default=None)
    entity: Optional[IdOptionalNameType] = None


class DomainAbuseDnsChange(ChangeType):
    domain: str
    removed: list[DnsRecord]
    added: list[DnsRecord]


class WhoisRecord(RFBaseModel):
    status: Optional[str] = None
    registrar_name: Optional[str] = None
    private_registration: Optional[bool] = None
    name_servers: Optional[list[str]] = []
    contact_email: Optional[str] = None
    created: Optional[datetime] = None


class WhoisContactRecord(ChangeType):
    telephone: Optional[str] = None
    street1: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    organization: Optional[str] = None
    name: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None
    country_code: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    created: Optional[datetime] = None


class DomainAbuseWhoisChange(ChangeType):
    domain: str
    old_record: Optional[WhoisRecord] = None
    new_record: Optional[WhoisRecord] = None
    removed_contacts: list[WhoisContactRecord]
    added_contacts: list[WhoisContactRecord]


class LogotypeInScreenshot(RFBaseModel):
    logotype_id: Optional[str] = None
    screenshot_id: Optional[str] = None
    url: HttpUrl


class DomainAbuseLogoTypeChange(ChangeType):
    domain: str
    removed: Optional[list[LogotypeInScreenshot]] = []
    added: Optional[list[LogotypeInScreenshot]] = []


class MaliciousAssessment(RFBaseModel):
    id_: str = Field(alias='id')
    level: int
    title: Optional[str] = None


class MaliciousDnsRecord(RFBaseModel):
    id_: Optional[str] = Field(alias='id', default=None)
    assessments: list[MaliciousAssessment]


class DomainAbuseMaliciousDnsChange(ChangeType):
    domain: str
    removed: Optional[list[MaliciousDnsRecord]] = []
    added: Optional[list[MaliciousDnsRecord]] = []


class ReregistrationRecord(RFBaseModel):
    registrar: Optional[str] = None
    registrar_name: Optional[str] = None
    iana_id: Optional[int] = None
    expiration: Optional[datetime] = None


class DomainAbuseReregistrationRecordChange(ChangeType):
    domain: str
    removed: Optional[ReregistrationRecord] = None
    added: Optional[ReregistrationRecord] = None


class Source(RFBaseModel):
    id_: str = Field(alias='id')
    name: str


class UrlAssessment(MaliciousAssessment):
    source: Source


class MaliciousUrlRecord(RFBaseModel):
    url: Optional[HttpUrl] = None
    assessments: list[UrlAssessment]


class DomainAbuseMaliciousUrlChange(ChangeType):
    domain: str
    removed: Optional[list[MaliciousUrlRecord]] = []
    added: Optional[list[MaliciousUrlRecord]] = []


class MentionedEntity(RFBaseModel):
    entity: IdOptionalNameType
    reference: Optional[str] = None
    fragment: Optional[str] = None


class ScreenshotMention(RFBaseModel):
    url: HttpUrl
    screenshot_id: str
    document: str
    analyzed: datetime
    mentioned_entities: list[MentionedEntity]


class DomainAbuseScreenshotMentions(ChangeType):
    domain: str
    added: list[ScreenshotMention]


class VulnerabilityAssessment(RFBaseModel):
    id_: str = Field(alias='id')
    level: int
    title: Optional[str] = None


class TriggeredRiskRule(RFBaseModel):
    id_: str = Field(alias='id')
    name: Optional[str] = None
    description: Optional[str] = None
    evidence_string: Optional[str] = None
    machine_name: Optional[str] = None
    timestamp: Optional[datetime] = None


class VulnerabilityLifecycleChange(ChangeType):
    added: Optional[VulnerabilityAssessment] = None
    removed: Optional[VulnerabilityAssessment] = None
    triggered_by_risk_rule: Optional[TriggeredRiskRule] = None


class Document(RFBaseModel):
    id_: str = Field(alias='id')
    content: str
    owner_id: str
    owner_name: Optional[str] = None
    published: datetime


class WatchList(RFBaseModel):
    id_: str = Field(alias='id')
    name: Optional[str] = None


class RepoAssessment(RFBaseModel):
    id_: str = Field(alias='id')
    level: int
    title: Optional[str] = None
    text_indicator: Optional[str] = None
    entity: Optional[IdOptionalNameType] = None


class CodeRepoLeakageEvidence(RFBaseModel):
    assessments: list[RepoAssessment]
    document: Document
    target_entities: list[IdOptionalNameType]
    watch_lists: list[WatchList]


class CodeRepoLeakageEvidenceChange(ChangeType):
    added: list[CodeRepoLeakageEvidence]


class TPRRiskEvidence(RFBaseModel):
    level: int
    evidence_string: Optional[str] = None
    timestamp: Optional[datetime] = None


class ThirdPartyAssessmentChange(ChangeType):
    risk_attribute: str
    added: Optional[TPRRiskEvidence] = None
    removed: Optional[TPRRiskEvidence] = None


class Assessment(RFBaseModel):
    level: int
    evidence_string: str
    timestamp: datetime


class AssessmentChange(ChangeType):
    risk_attribute: str
    removed: Optional[Assessment] = None
    added: Optional[Assessment] = None


TYPE_MAPPING = {
    'assignee_change': AssigneeChange,
    'status_change': StatusChange,
    'priority_change': PriorityChange,
    'reopen_strategy_change': OldNewOptionalType,
    'title_change': OldNewOptionalType,
    'entities_change': AddedRemovedTypeEntities,
    'related_entities_change': AddedRemovedTypeEntities,
    'description_change': OldNewOptionalType,
    'external_id_change': OldNewOptionalType,
    'comment_change': CommentChange,
    'action_change': AddedRemovedList,
    'assessment_ids_change': AddedRemovedList,
    'dns_change': DomainAbuseDnsChange,
    'whois_change': DomainAbuseWhoisChange,
    'logotype_in_screenshot_change': DomainAbuseLogoTypeChange,
    'malicious_dns_change': DomainAbuseMaliciousDnsChange,
    'reregistration_change': DomainAbuseReregistrationRecordChange,
    'malicious_url_change': DomainAbuseMaliciousUrlChange,
    'screenshot_mentions_change': DomainAbuseScreenshotMentions,
    'lifecycle_in_cve_change': VulnerabilityLifecycleChange,
    'evidence_change': CodeRepoLeakageEvidenceChange,
    'tpr_assessment_change': ThirdPartyAssessmentChange,
    'assessment_change': AssessmentChange,
}


class PanelLogV2(RFBaseModel):
    id_: str = Field(alias='id')
    author_id: Optional[str] = None
    author_name: Optional[str] = None
    created: datetime
    changes: list

    @model_validator(mode='before')
    @classmethod
    def validate_changes(cls, data):
        """Validate each panel_log_v2 changes based on the supported changes.

        The list of changes is in ``TYPE_MAPPING``. Skip unsupported changes.
        """
        new_changes = [
            model_type.model_validate(change)
            for change in data.get('changes', [])
            if (change_type := change.get('type')) and (model_type := TYPE_MAPPING.get(change_type))
        ]
        data['changes'] = new_changes
        return data
