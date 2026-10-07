const userAgent = process.env.npm_config_user_agent || "";

if (!userAgent.includes("pnpm/")) {
  console.error("Panama PortOps-AI usa pnpm por defecto. Ejecute: corepack enable && pnpm install");
  process.exit(1);
}
