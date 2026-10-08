"""Explicit capability checks for legacy routes; display roles grant nothing."""

RETIRED_MUTATIONS = {
 ('POST','/api/admin/users'),('POST','/api/admin/delete-user'),('POST','/api/admin/revoke-sessions'),
 ('POST','/api/v1/system/secrets'),
 ('POST','/api/v1/models/promote'),
}

def retired(method,path):
 return (method,path) in RETIRED_MUTATIONS

def required_capability(method,path):
 if path.startswith('/api/workspace/') or path.startswith('/api/v1/auth/') and not path.startswith('/api/v1/auth/users'):
  return None
 if path.startswith('/api/admin/') or path.startswith('/api/v1/auth/users'):
  return 'audit.read' if path=='/api/admin/governance' else 'iam.write'
 if path.startswith('/api/v1/audit/'):
  return 'audit.verify' if path.endswith('/verify') else 'audit.read'
 if path.startswith('/api/v1/telemetry/'):
  return 'audit.read' if method=='GET' else 'forecast.read'
 if path.startswith('/api/history/') or path in {'/api/extensibility/simulate-external-feature'}:return 'forecast.read'
 if path.startswith('/api/diagnostics/') or path in {'/api/models/compare','/api/models/diagnostics','/api/v1/models/benchmark','/api/v1/models/registry','/api/v1/models/benchmark-8'}:return 'models.read'
 if path in {'/api/v1/data/sources','/api/v1/data/quality/summary','/api/v1/data-platform/manifest','/api/v1/data/catalog/manifest','/api/v1/features/catalog','/api/lakehouse/catalog'}:return 'datasets.read'
 if path.startswith('/api/v1/system/secrets'):return 'secrets.write'
 if path=='/api/v1/system/provider-test':return 'services.write'
 if path.startswith('/api/v1/infra/config'):return 'config.read' if method=='GET' else 'config.write'
 if path.startswith('/api/v1/integrations/wazuh/'):return 'services.write'
 if path=='/api/mcp/souls':return 'workspace.read' if method=='GET' else 'agents.write'
 if path in {'/api/mcp/execute-tool','/api/mcp/langgraph-route','/api/v1/mcp/execute','/api/v1/agents/chat','/api/v1/agents/reasoning-chat'}:return 'agents.write'
 if path in {'/api/simulation/run','/api/v1/simulations/run','/api/simulation/synthetic-dataset'}:return 'simulation.run'
 if path in {'/api/simulation/history','/api/v1/simulations/history','/api/simulation/quotas','/api/v1/simulations/quotas'}:return 'simulation.run'
 if path=='/api/export/dataset':return 'simulation.export'
 if path in {'/api/models/reproducible-train'}:return 'models.train'
 if path=='/api/v1/models/promote':return 'models.review'
 if path in {'/api/v1/models/register','/api/v1/models/deploy'}:return 'models.train'
 if method!='GET' and path in {'/api/config','/api/infrastructure/database/test-connection','/api/v1/framework/profile','/api/models/presets'}:return 'config.write'
 if method!='GET' and path=='/api/v1/guardrails/policies':return 'iam.write'
 if method!='GET' and path in {'/api/lakehouse/query','/api/v1/data/quality/validate','/api/privacy/simulate-anonymization'}:return 'datasets.write'
 return None

# Keep public demonstrations accessible; logged-in accounts still obey their role.
PUBLIC_DEMO_ROUTES={'/api/simulation/run','/api/simulation/synthetic-dataset','/api/simulation/history',
 '/api/simulation/quotas','/api/export/dataset','/api/lakehouse/query','/api/v1/data/quality/validate',
 '/api/privacy/simulate-anonymization','/api/v1/agents/chat','/api/v1/agents/reasoning-chat','/api/v1/mcp/execute',
 '/api/v1/telemetry/feedback','/api/v1/audit/worm/verify','/api/v1/audit/events','/api/v1/telemetry/summary'}
