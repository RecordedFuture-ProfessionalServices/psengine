from psengine.asi import AttackSurfaceMgr

mgr = AttackSurfaceMgr()

projects = mgr.fetch_projects()
project_id = None

print('Projects: \n')
print(projects)

for project in projects.data:
    if project.title == 'Bank Demo 2025':
        project_id = project.id_
        break

print(f'\nProject ID: {project_id}\n')

print('Exposures: \n')
exposures = mgr.search_exposures(
    project_id, filter_severity_exact='critical'
)

print(exposures)
