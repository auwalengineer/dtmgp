import { z } from "zod";

const environmentSchema = z.object({
  apiBaseUrl: z.string(),
  environment: z.enum(["development", "staging", "production"]),
});

export type AppEnvironment = z.infer<typeof environmentSchema>;

const buildEnvironment: AppEnvironment = environmentSchema.parse({
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || "",
  environment: import.meta.env.VITE_APP_ENV || "development",
});

export async function loadEnvironment(): Promise<AppEnvironment> {
  const runtimeUrl = import.meta.env.VITE_RUNTIME_CONFIG_URL;
  if (!runtimeUrl) return buildEnvironment;

  try {
    const response = await fetch(runtimeUrl, { cache: "no-store" });
    if (!response.ok) return buildEnvironment;
    return environmentSchema.parse(await response.json());
  } catch {
    return buildEnvironment;
  }
}
