## Introduction

The `AttackSurfaceMgr` class of the `asi` module allows you to fetch or search for intelligence (assets and signatures) around your exposed infrastructure.

See the [**API Reference**](../api/asi/asi_mgr.md) for internal details of the module.

## Examples

{! modules/_includes/examples_asi_warning.md !}

#### 1: Search for critical exposures

In this example, we are listing all the projects we have available and search for the "Bank Demo 2025" project ID. This step is required only if you don't know the project ID already or if you want to do the same operation on all the projects you have access to.

After finding the project ID, we are going to search for the all the exposures that have a severity of `critical`. Printing the list of exposures will automatically sort them by severity and number of assets impacted.

```python
--8 < --'docs/examples/asi/example_1.py'
```

The output is:

```
Projects:

Name: Bank Demo 2025 (Small), Id: 7c2d06d7-0c4b-4d0d-bc97-f81dcdc276de, Enabled: True
Name: Bank Demo 2025, Id: 10b94298-e411-4d0a-b0ad-bf81b1948f84, Enabled: True
Name: Partner Shared Demo, Id: 3ce6292b-29be-4199-9024-231818e384a4, Enabled: True

Project ID: 10b94298-e411-4d0a-b0ad-bf81b1948f84

Exposures:

Name: CVE-2022-2551 - Duplicator – WordPress Migration Plugin <= 1.4.7 - Unauthenticated Backup Download, Id: CVE-2022-2551, Severity: critical, Asset Count: 5
Name: Jboss Application Server - Remote Code Execution (CVE-2017-12149), Id: CVE-2017-12149, Severity: critical, Asset Count: 4
Name: CVE-2022-0651 - WP Statistics <= 13.1.5 - Unauthenticated Blind SQL Injection via current_page_type, Id: CVE-2022-0651, Severity: critical, Asset Count: 3
Name: CVE-2022-25148 - WP Statistics <= 13.1.5 - Unauthenticated SQL Injection, Id: CVE-2022-25148, Severity: critical, Asset Count: 3
Name: CVE-2022-25149 - WP Statistics <= 13.1.5 - Unauthenticated Blind SQL Injection via IP, Id: CVE-2022-25149, Severity: critical, Asset Count: 3
Name: WordPress Ultimate Member Plugin <2.6.7 - Privilege Escalation (CVE-2023-3460), Id: CVE-2023-3460, Severity: critical, Asset Count: 3
Name: Forminator <= 1.24.6 - Unauthenticated Arbitrary File Upload (CVE-2023-4596), Id: CVE-2023-4596, Severity: critical, Asset Count: 3
Name: Microsoft Windows 'HTTP.sys' - Remote Code Execution (CVE-2015-1635), Id: CVE-2015-1635, Severity: critical, Asset Count: 2
Name: CVE-2020-25213 - File Manager <= 6.8 - Arbitrary File Upload/Remote Code Execution, Id: CVE-2020-25213, Severity: critical, Asset Count: 2
Name: CVE-2020-36155 - Ultimate Member <= 2.1.11 - Unauthenticated Privilege Escalation via User Meta, Id: CVE-2020-36155, Severity: critical, Asset Count: 2
```

#### 2: Get open ports for a specific asset 

In this example we have an asset `www.theology.bsu.by` of which we need to find all the open ports. We use the `fetch_asset` method using the `additional_fields` parameter to enrich the asset with `open_tcp_ports` and `open_udp_ports`. Then, we print the ports that has been found.

```python
--8 < --'docs/examples/asi/example_2.py'
```

The output is:

```
Name: www.theology.bsu.by, Type: domain, Exposure Score: 99

www.theology.bsu.by has open ports: 21, 25, 80, 110, 143, 443, 465, 587, 993, 1500, 2200, 2525, 10050, 1501                                                                                 
```

#### 3: Get all the assets that are exposed to WordPress CVE-2022-2551

```python
--8 < --'docs/examples/asi/example_3.py'
```

The output is:

```
staff.basij.sharif.edu is affected, at http://staff.basij.sharif.edu:80/wp-content/plugins/duplicator/readme.txt
negociosdev.ucab.edu.ve is affected, at https://negociosdev.ucab.edu.ve:443/wp-content/plugins/duplicator/readme.txt
imt.ucv.ve is affected, at http://imt.ucv.ve:80/wp-content/plugins/duplicator/readme.txt
deneb.ucv.ve is affected, at http://deneb.ucv.ve:80/wp-content/plugins/duplicator/readme.txt
basij.sharif.ir is affected, at http://basij.sharif.ir:80/wp-content/plugins/duplicator/readme.txt
```

