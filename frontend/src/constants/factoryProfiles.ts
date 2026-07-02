/** Human-readable names for QA Factory specialist profiles (Agentic QA UI). */

export const FACTORY_PROFILE_DISPLAY_NAMES: Record<string, string> = {
  'qa-orchestrator': 'QA Orchestrator',
  'qa-journey-planner': 'Journey Planner',
  'qa-test-gen': 'Test Generator',
  'qa-dispatcher': 'Dispatcher',
  'qa-reporter': 'Reporter',
  'qa-change-detector': 'Change Detector',
  'qa-healer': 'Healer',
  factory_bridge: 'Factory Node',
  hermes_bridge: 'Factory Node',
  system: 'System',
};

export function factoryProfileDisplayName(profile?: string | null): string {
  if (!profile) return 'System';
  return FACTORY_PROFILE_DISPLAY_NAMES[profile] ?? profile;
}
