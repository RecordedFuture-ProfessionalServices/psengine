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

from functools import total_ordering
from typing import Optional

from pydantic import Field, NonNegativeInt, PositiveInt, model_validator

from ..common_models import RFBaseModel
from ..constants import DEFAULT_LIMIT, TIMESTAMP_STR
from ..playbook_alerts.markdown.markdown import _markdown_playbook_alert
from .models import (
    CodeRepoEvidencePanel,
    CodeRepoPanelStatus,
    CyberVulnerabilityEvidencePanel,
    CyberVulnerabilityPanelStatus,
    DatetimeRange,
    DomainAbuseEvidenceDns,
    DomainAbuseEvidenceSummary,
    DomainAbuseEvidenceWhois,
    DomainAbusePanelStatus,
    IdentityEvidencePanel,
    IdentityPanelStatus,
    TPREvidencePanel,
    TPRPanelStatus,
)
from .models.panel_log import (
    CodeRepoLeakageEvidenceChange,
    DomainAbuseDnsChange,
    DomainAbuseLogoTypeChange,
    DomainAbuseMaliciousDnsChange,
    DomainAbuseMaliciousUrlChange,
    DomainAbuseReregistrationRecordChange,
    DomainAbuseScreenshotMentions,
    DomainAbuseWhoisChange,
    PanelLogV2,
    ThirdPartyAssessmentChange,
    VulnerabilityLifecycleChange,
)
from .models.panel_status import PanelAction, PanelStatus
from .pa_category import PACategory


@total_ordering
class PBA_Generic(RFBaseModel):
    """Base Model for Playbook Alerts. Removes the deprecated panel_log.
    This model is intended to be inherited and should not be used on its own.

    Methods:
        __hash__:
            Returns hash value based on ``playbook_alert_id`` and updated timestamp in panel status.

        __eq__:
            Checks equality between two BasePlaybookAlert instances based on ``playbook_alert_id``
            and updated timestamp in panel status.

        __gt__:
            Defines a greater-than comparison between two ``BasePlaybookAlert`` instances based on
            ``playbook_alert_id`` and updated timestamp in panel status.

        __str__:
            Returns a string representation of the BasePlaybookAlert instance with:
            ``playbook_alert_id``, updated timestamp, case rule label, and status.

            .. code-block:: python

                >>> print(playbook_alert)
                Playbook Alert ID: task:a1ccb1c8-5554-42af, Updated: 2024-05-21 10:42:30AM,
                Category: Third Party Risk, Lookup Status: New

    Total Ordering:
        The ordering of BasePlaybookAlert instances is determined primarily by the updated timestamp
        of the panel status. If two instances have the same updated timestamp, their
        ``playbook_alert_id`` is used as a secondary criterion for ordering.
    """

    playbook_alert_id: str
    panel_log_v2: Optional[list[PanelLogV2]] = []
    panel_status: Optional[PanelStatus] = Field(default_factory=PanelStatus)

    category: str = PACategory.UNMAPPED_ALERT.value

    @model_validator(mode='before')
    @classmethod
    def remove_panel_log(cls, data):
        """Remove panel_log since it is deprecated."""
        if 'panel_log' in data:
            del data['panel_log']
        return data

    def __hash__(self):
        return hash((self.playbook_alert_id, self.panel_status.updated))

    def __eq__(self, other: 'PBA_Generic'):
        return (self.playbook_alert_id, self.panel_status.updated) == (
            other.playbook_alert_id,
            other.panel_status.updated,
        )

    def __gt__(self, other: 'PBA_Generic'):
        return (self.panel_status.updated, self.playbook_alert_id) > (
            other.panel_status.updated,
            other.playbook_alert_id,
        )

    def __str__(self):
        return (
            f'Playbook Alert ID: {self.playbook_alert_id}, '
            f'Updated: {self.panel_status.updated.strftime(TIMESTAMP_STR)}, '
            f'Category: {self.panel_status.case_rule_label}, '
            f'Lookup Status: {self.panel_status.status}'
        )

    def markdown(
        self,
        html_tags: bool = True,
        character_limit: Optional[int] = None,
        defang_iocs: bool = False,
    ):
        """Markdown implementation for Playbook Alerts."""
        return _markdown_playbook_alert(
            self, html_tags=html_tags, character_limit=character_limit, defang_iocs=defang_iocs
        )

    def _get_changes(self, change_type):
        """Filter for a specific change type from the v2 panel log."""
        changes = [obj.changes for obj in self.panel_log_v2]
        changes = [x for y in changes for x in y]
        return list(filter(lambda x: isinstance(x, change_type), changes))


class PBA_CodeRepoLeakage(PBA_Generic):
    """Model for Code Repo Leakage. Inherit behaviours from BasePlaybookAlert."""

    __doc__ = __doc__ + '\n\n' + PBA_Generic.__doc__  # noqa: A003

    category: str = PACategory.CODE_REPO_LEAKAGE.value

    panel_status: Optional[CodeRepoPanelStatus] = Field(default_factory=CodeRepoPanelStatus)
    panel_evidence_summary: Optional[CodeRepoEvidencePanel] = Field(
        default_factory=CodeRepoEvidencePanel
    )

    @property
    def log_code_repo_leakage_evidence_changes(self) -> list:
        """Code Repo Leakage Evidence change."""
        return self._get_changes(CodeRepoLeakageEvidenceChange)


class PBA_ThirdPartyRisk(PBA_Generic):
    """Model for Third Party Risk. Inherit behaviours from BasePlaybookAlert."""

    __doc__ = __doc__ + '\n\n' + PBA_Generic.__doc__  # noqa: A003

    category: str = PACategory.THIRD_PARTY_RISK.value

    panel_status: Optional[TPRPanelStatus] = Field(default_factory=TPRPanelStatus)
    panel_evidence_summary: Optional[TPREvidencePanel] = Field(default_factory=TPREvidencePanel)

    @property
    def log_third_party_assessment_changes(self) -> list:
        """Third Party Assessment change."""
        return self._get_changes(ThirdPartyAssessmentChange)


class PBA_CyberVulnerability(PBA_Generic):
    """Model for Cyber Vulnerability. Inherit behaviours from BasePlaybookAlert."""

    __doc__ = __doc__ + '\n\n' + PBA_Generic.__doc__  # noqa: A003

    category: str = PACategory.CYBER_VULNERABILITY.value

    panel_status: Optional[CyberVulnerabilityPanelStatus] = Field(
        default_factory=CyberVulnerabilityPanelStatus
    )
    panel_evidence_summary: Optional[CyberVulnerabilityEvidencePanel] = Field(
        default_factory=CyberVulnerabilityEvidencePanel
    )

    @property
    def lifecycle_stage(self) -> str:
        """Get playbook alert lifecycle_stage."""
        if stage := self.panel_status.lifecycle_stage:
            return stage
        return self.panel_evidence_summary.summary.lifecycle_stage

    @property
    def log_vulnerability_lifecycle_changes(self) -> list:
        """Get ``VulnerabilityLifecycleChange`` log changes."""
        return self._get_changes(VulnerabilityLifecycleChange)


class PBA_IdentityNovelExposure(PBA_Generic):
    """Model for Identity Exposure. Inherit behaviours from BasePlaybookAlert."""

    __doc__ = __doc__ + '\n\n' + PBA_Generic.__doc__  # noqa: A003

    category: str = PACategory.IDENTITY_NOVEL_EXPOSURES.value

    panel_status: Optional[IdentityPanelStatus] = Field(default_factory=IdentityPanelStatus)
    panel_evidence_summary: Optional[IdentityEvidencePanel] = Field(
        default_factory=IdentityEvidencePanel
    )

    @property
    def assessment_names(self) -> list[str]:
        """Assessments contain name and criticality, this returns all assessment names.

        Returns:
            List[str]: assessments names or [] if not found
        """
        if not self.panel_evidence_summary or not self.panel_evidence_summary.assessments:
            return []
        return [assessment.name for assessment in self.panel_evidence_summary.assessments]

    @property
    def technology_names(self) -> list[str]:
        """Novel Identity Exposure: Return the technologies names list.

        Returns:
            list[str]: List of technologies names
        """
        if not self.panel_evidence_summary or not self.panel_evidence_summary.technologies:
            return []
        return [tech.name for tech in self.panel_evidence_summary.technologies]


class PBA_DomainAbuse(PBA_Generic):
    """Model for Domain Abuse. Inherit behaviours from BasePlaybookAlert."""

    __doc__ = __doc__ + '\n\n' + PBA_Generic.__doc__  # noqa: A003

    _images: Optional[dict] = {}

    category: str = PACategory.DOMAIN_ABUSE.value

    panel_action: Optional[list[PanelAction]] = []
    panel_status: Optional[DomainAbusePanelStatus] = Field(default_factory=DomainAbusePanelStatus)
    panel_evidence_summary: Optional[DomainAbuseEvidenceSummary] = Field(
        default_factory=DomainAbuseEvidenceSummary
    )
    panel_evidence_dns: Optional[DomainAbuseEvidenceDns] = Field(
        default_factory=DomainAbuseEvidenceDns
    )
    panel_evidence_whois: Optional[DomainAbuseEvidenceWhois] = Field(
        default_factory=DomainAbuseEvidenceWhois
    )

    def store_image(self, image_id: str, image_bytes: bytes) -> None:
        """Domain Abuse: store image bytes in ``self._images`` dictionary.

        Args:
            image_id (str): image id
            image_bytes (bytes): image bytes

        Raises:
            ValueError: if the image_id is not present in alert screenshots list
        """
        image_id_matches = list(
            filter(
                lambda x: x.image_id == image_id,
                self.panel_evidence_summary.screenshots,
            )
        )
        if len(image_id_matches) == 0:
            raise ValueError(
                f"Alert '{self.playbook_alert_id}' does not contain image id: '{image_id}'"
            )
        image_info = image_id_matches[0]
        self._images[image_id] = {}
        self._images[image_id]['description'] = image_info.description
        self._images[image_id]['created'] = image_info.created
        self._images[image_id]['image_bytes'] = image_bytes

    @property
    def image_ids(self) -> list:
        """Domain Abuse: get the playbook alert image ids.

        Returns:
            list: Alert image ids or empty list if not found
        """
        ids = []
        if self.panel_evidence_summary.screenshots:
            ids = [screenshot.image_id for screenshot in self.panel_evidence_summary.screenshots]
        return ids

    @property
    def images(self) -> dict:
        """Domain Abuse: get raw bytes of the screenshots.

        This data is stored in the following format:

        .. code-block::

            {
                image_id : {
                    'description': "awesome image description",
                    'created': "date",
                    'image_bytes': b'xyz'
                }
            }

        Returns:
            dict: Alert images raw bytes or {} if not found
        """
        return self._images

    @property
    def log_dns_changes(self) -> list:
        """DNS change."""
        return self._get_changes(DomainAbuseDnsChange)

    @property
    def log_whois_changes(self) -> list:
        """WHOIS change."""
        return self._get_changes(DomainAbuseWhoisChange)

    @property
    def log_logotype_changes(self) -> list:
        """Logotype change."""
        return self._get_changes(DomainAbuseLogoTypeChange)

    @property
    def log_malicious_dns_changes(self) -> list:
        """Malaicious DNS change."""
        return self._get_changes(DomainAbuseMaliciousDnsChange)

    @property
    def log_reregistration_changes(self) -> list:
        """Reregistration change."""
        return self._get_changes(DomainAbuseReregistrationRecordChange)

    @property
    def log_malicious_url_changes(self) -> list:
        """Malicious URL change."""
        return self._get_changes(DomainAbuseMaliciousUrlChange)

    @property
    def log_screenshot_mentions_changes(self) -> list:
        """Screenshot mentions change."""
        return self._get_changes(DomainAbuseScreenshotMentions)


class SearchIn(RFBaseModel):
    """Model for payload sent to ``/search`` endpoint."""

    from_: Optional[NonNegativeInt] = Field(alias='from', default=None)
    limit: Optional[PositiveInt] = DEFAULT_LIMIT
    order_by: Optional[str] = None
    direction: Optional[str] = None
    entity: Optional[list] = None
    statuses: Optional[list[str]] = None
    priority: Optional[list[str]] = None
    category: Optional[list[str]] = None
    assignee: Optional[list[str]] = None
    created_range: Optional[DatetimeRange] = None
    updated_range: Optional[DatetimeRange] = None


class PreviewAlertOut(PanelStatus):
    """Model for payload received by GET ``/common/{alert_id}`` endpoint."""

    playbook_alert_id: str
    title: str
    category: str


class UpdateAlertIn(RFBaseModel):
    """Model for payload sent to PUT ``/common/{playbook_alert_id}`` endpoint."""

    priority: Optional[str] = None
    status: Optional[str] = None
    assignee: Optional[str] = None
    log_entry: Optional[str] = None
    reopen: Optional[str] = None
    added_actions_taken: Optional[list[str]] = None
    removed_actions_taken: Optional[list[str]] = None


class LookupAlertIn(RFBaseModel):
    """Model for playbook alert POST ``{playbook_alert_id}`` endpoints."""

    panels: Optional[list] = None
