## Data Leakage on Code Repository

### Summary

**ID:** task:39b78e8c-5fb7-42dc-b9e4-bf078ecc7710  
**Created:** 2025-07-14 15:34:07  
**Updated:** 2025-07-14 15:37:00  
**Status:** New  
**Priority:** Moderate  
[API](https://api.recordedfuture.com/playbook-alert/code_repo_leakage/task:39b78e8c-5fb7-42dc-b9e4-bf078ecc7710) | [Portal](https://app.recordedfuture.com/portal/playbook-alerts/task:39b78e8c-5fb7-42dc-b9e4-bf078ecc7710)

### Targets

reddit.com

### Repository

**Owner:** laasya2505  
**URL:** https://github.com/laasya2505/reddit-persona  

### Assessments

**Published:** 2025-07-14 15:36:52  
**Assessment targets:** reddit.com  
**Possible Key Leak:** username  
**Watch List Entity Mention on GitHub:** reddit.com  
**Commit:** https://github.com/laasya2505/reddit-persona/commit/dd777afda2a128e5198f6f94f53de4c64ebad409  
**Content:**

> ++\#\#\# API Endpoints Used+\- \`https://www.reddit.com/user/{username}/about/.json\` \- Account information+\- \`https://www.reddit.com/user/{username}/submitted/.json\` \- User posts+\- \`https://www.reddit.com/user/{username}/comments/.json\` \- User comments  

---

**Published:** 2025-07-14 15:33:53  
**Possible Key Leak:** token  
**Commit:** https://github.com/laasya2505/reddit-persona/commit/4cd88cba7882986944cca62a7901041581ac9aa1  
**Content:**

> + })++ \# Get the &#x27;after&#x27; token for pagination+ after = data.get(&#x27;data&#x27;, {}).get(&#x27;after&#x27;)+ if not after:  

---

**Published:** 2025-07-14 15:33:53  
**Assessment targets:** reddit.com  
**Possible Key Leak:** username  
**Watch List Entity Mention on GitHub:** reddit.com  
**Commit:** https://github.com/laasya2505/reddit-persona/commit/4cd88cba7882986944cca62a7901041581ac9aa1  
**Content:**

> ++Usage:+python reddit\\_persona.py https://www.reddit.com/user/username/+&quot;&quot;&quot;+  

---

**Published:** 2025-07-14 15:33:53  
**Assessment targets:** reddit.com  
**Possible Key Leak:** username  
**Watch List Entity Mention on GitHub:** reddit.com  
**Commit:** https://github.com/laasya2505/reddit-persona/commit/4cd88cba7882986944cca62a7901041581ac9aa1  
**Content:**

> ++Username: amyaurora+Profile URL: https://www.reddit.com/user/amyaurora/+Generated: 2025\-07\-14 20:26:22+  

---


