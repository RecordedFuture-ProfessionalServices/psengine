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


class Assignee(RFBaseModel):
    id_: str = Field(alias='id')
    name: str


class AssigneeChange(ChangeType):
    old: Assignee | None = None
    new: Assignee | None = None


class DnsRecord(RFBaseModel):
    type_: str | None = Field(alias='type', default=None)
    entity: IdOptionalNameType | None = None


class DomainAbuseDnsChange(ChangeType):
    domain: str
    removed: list[DnsRecord]
    added: list[DnsRecord]


class WhoisRecord(RFBaseModel):
    status: str | None = None
    registrar_name: str | None = None
    private_registration: bool | None = None
    name_servers: list[str] | None = []
    contact_email: str | None = None
    created: datetime | None = None


class WhoisContactRecord(ChangeType):
    telephone: str | None = None
    street1: str | None = None
    state: str | None = None
    postal_code: str | None = None
    organization: str | None = None
    name: str | None = None
    fax: str | None = None
    email: str | None = None
    country_code: str | None = None
    country: str | None = None
    city: str | None = None
    created: datetime | None = None


class DomainAbuseWhoisChange(ChangeType):
    domain: str
    old_record: WhoisRecord | None = None
    new_record: WhoisRecord | None = None
    removed_contacts: list[WhoisContactRecord]
    added_contacts: list[WhoisContactRecord]


class LogotypeInScreenshot(RFBaseModel):
    logotype_id: str | None = None
    screenshot_id: str | None = None
    url: HttpUrl


class DomainAbuseLogoTypeChange(ChangeType):
    domain: str
    removed: list[LogotypeInScreenshot] | None = []
    added: list[LogotypeInScreenshot] | None = []


class MaliciousAssessment(RFBaseModel):
    id_: str = Field(alias='id')
    level: int
    title: str | None = None


class MaliciousDnsRecord(RFBaseModel):
    id_: str | None = Field(alias='id', default=None)
    assessments: list[MaliciousAssessment]


class DomainAbuseMaliciousDnsChange(ChangeType):
    domain: str
    removed: list[MaliciousDnsRecord] | None = []
    added: list[MaliciousDnsRecord] | None = []


class ReregistrationRecord(RFBaseModel):
    registrar: str | None = None
    registrar_name: str | None = None
    iana_id: int | None = None
    expiration: datetime | None = None


class DomainAbuseReregistrationRecordChange(ChangeType):
    domain: str
    removed: ReregistrationRecord | None = None
    added: ReregistrationRecord | None = None


class Source(RFBaseModel):
    id_: str = Field(alias='id')
    name: str


class UrlAssessment(MaliciousAssessment):
    source: Source


class MaliciousUrlRecord(RFBaseModel):
    url: HttpUrl | None = None
    assessments: list[UrlAssessment]


class DomainAbuseMaliciousUrlChange(ChangeType):
    domain: str
    removed: list[MaliciousUrlRecord] | None = []
    added: list[MaliciousUrlRecord] | None = []


class MentionedEntity(RFBaseModel):
    entity: IdOptionalNameType
    reference: str | None = None
    fragment: str | None = None


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
    title: str | None = None


class TriggeredRiskRule(RFBaseModel):
    id_: str = Field(alias='id')
    name: str | None = None
    description: str | None = None
    evidence_string: str | None = None
    machine_name: str | None = None
    timestamp: datetime | None = None


class VulnerabilityLifecycleChange(ChangeType):
    added: VulnerabilityAssessment | None = None
    removed: VulnerabilityAssessment | None = None
    triggered_by_risk_rule: TriggeredRiskRule | None = None


class Document(RFBaseModel):
    id_: str = Field(alias='id')
    content: str
    owner_id: str
    owner_name: str | None = None
    published: datetime


class WatchList(RFBaseModel):
    id_: str = Field(alias='id')
    name: str | None = None


class RepoAssessment(RFBaseModel):
    id_: str = Field(alias='id')
    level: int
    title: str | None = None
    text_indicator: str | None = None
    entity: IdOptionalNameType | None = None


class CodeRepoLeakageEvidence(RFBaseModel):
    assessments: list[RepoAssessment]
    document: Document
    target_entities: list[IdOptionalNameType]
    watch_lists: list[WatchList]


class CodeRepoLeakageEvidenceChange(ChangeType):
    added: list[CodeRepoLeakageEvidence]


class TPRRiskEvidence(RFBaseModel):
    level: int
    evidence_string: str | None = None
    timestamp: datetime | None = None


class ThirdPartyAssessmentChange(ChangeType):
    risk_attribute: str
    added: TPRRiskEvidence | None = None
    removed: TPRRiskEvidence | None = None


class Assessment(RFBaseModel):
    level: int
    evidence_string: str
    timestamp: datetime


class AssessmentChange(ChangeType):
    risk_attribute: str
    removed: Assessment | None = None
    added: Assessment | None = None


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
    author_id: str | None = None
    author_name: str | None = None
    created: datetime
    changes: list

    @model_validator(mode='before')
    @classmethod
    def validate_changes(cls, data):
        """Validate each panel_log_v2 changes based on the supported changes.

        The list of changes is in `TYPE_MAPPING`. Skip unsupported changes.
        """
        new_changes = [
            model_type.model_validate(change)
            for change in data.get('changes', [])
            if (change_type := change.get('type')) and (model_type := TYPE_MAPPING.get(change_type))
        ]
        data['changes'] = new_changes
        return data
