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

from pydantic import Field, model_validator

from ....common_models import RFBaseModel
from .code_repo import CodeRepoLeakageEvidenceChange
from .domain_abuse import (
    DomainAbuseDnsChange,
    DomainAbuseLogoTypeChange,
    DomainAbuseMaliciousDnsChange,
    DomainAbuseMaliciousUrlChange,
    DomainAbuseReregistrationRecordChange,
    DomainAbuseScreenshotMentions,
    DomainAbuseWhoisChange,
)
from .generic import (
    AddedRemovedList,
    AddedRemovedTypeEntities,
    AssigneeChange,
    CommentChange,
    OldNewOptionalType,
    OnwardActionsAddedChange,
    OnwardActionsRemovedChange,
    PriorityChange,
    StatusChange,
)
from .geopolitics import ClusterChangeAdded, EvidenceClusterChanges
from .malicious_sites import (
    AttackerAddedChange,
    ForSaleChange,
    LogoHashChange,
    MaliciousSitesAttackerAddedChange,
    MaliciousSitesDnsChange,
    MaliciousSitesLogoChange,
    MaliciousSitesMaliciousDnsChange,
    MaliciousSitesMaliciousUrlChange,
    MaliciousSitesReregistrationChange,
    MaliciousSitesScreenshotMentionChange,
    MaliciousSitesWhoisChange,
    ParkedChange,
    PhishingMaliciousBehaviorChange,
    PhishingVerdictChange,
    SuggestedTakedownChange,
)
from .tpr import AssessmentChange, ThirdPartyAssessmentChange
from .vulnerability import VulnerabilityLifecycleChange

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
    'onward_actions_removed_change': OnwardActionsRemovedChange,
    'onward_actions_added_change': OnwardActionsAddedChange,
    'phishing_malicious_behavior_change': PhishingMaliciousBehaviorChange,
    'attacker_added_change': AttackerAddedChange,
    'malicious_sites_attacker_added_change': MaliciousSitesAttackerAddedChange,
    'malicious_sites_dns_change': MaliciousSitesDnsChange,
    'malicious_sites_whois_change': MaliciousSitesWhoisChange,
    'malicious_sites_malicious_dns_change': MaliciousSitesMaliciousDnsChange,
    'malicious_sites_reregistration_change': MaliciousSitesReregistrationChange,
    'malicious_sites_malicious_url_change': MaliciousSitesMaliciousUrlChange,
    'malicious_sites_screenshot_mention_change': MaliciousSitesScreenshotMentionChange,
    'malicious_sites_logo_change': MaliciousSitesLogoChange,
    'for_sale_change': ForSaleChange,
    'parked_change': ParkedChange,
    'logo_hash_change': LogoHashChange,
    'phishing_verdict_change': PhishingVerdictChange,
    'suggested_takedown_change': SuggestedTakedownChange,
    'evidence_changes': EvidenceClusterChanges,
    'cluster_change_added': ClusterChangeAdded,
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
