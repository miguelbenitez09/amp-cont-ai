"""Compatibility names derived from the authoritative workspace capabilities."""
CAPABILITY_PERMISSIONS={
 'workspace.read':[], 'config.read':['system.config.read'], 'config.write':['system.config.write'],
 'iam.write':['user.read','user.create','user.disable','role.read','role.assign'],
 'audit.read':['audit.read'],'audit.verify':['audit.verify'], 'secrets.write':['secret.read','secret.rotate'],
 'services.write':['service.test'],'agents.write':['agent.execute'],'modules.write':['module.configure'],
 'datasets.read':['data.source.read','data.dataset.read','data.dataset.export','feature.read'],
 'datasets.write':['data.source.create','data.ingest.execute','data.dataset.delete','feature.create'],
 'datasets.review':['data.dataset.review'],'models.read':['experiment.read','model.read'],
 'models.train':['experiment.create','experiment.execute','model.train','model.register'],
 'models.predict':['model.predict'],'models.review':['model.review'],
 'forecast.read':['forecast.read'],'simulation.run':['simulation.run'],'simulation.export':['simulation.export'],
}
def permission_names(capabilities):
 return sorted({permission for cap in capabilities for permission in CAPABILITY_PERMISSIONS.get(cap,[])})
