import { create } from 'zustand';
import type { Agent } from '@/lib/types';

interface AgentState {
  agents: Agent[];
  activeAgentId: string | null;

  activeAgent: () => Agent | undefined;

  setAgents: (agents: Agent[]) => void;
  setActiveAgent: (id: string | null) => void;
  updateAgentStatus: (id: string, status: Agent['status']) => void;
}

const DEFAULT_AGENTS: Agent[] = [
  {
    id: 'network-analyst',
    name: 'Network Analyst',
    description: 'Discovers and analyzes Meraki networks',
    status: 'active',
    capabilities: ['discovery', 'analysis', 'diagnostics', 'inventory'],
    icon: 'Search',
  },
  {
    id: 'meraki-specialist',
    name: 'Meraki Specialist',
    description: 'Configures SSIDs, VLANs, ACLs, and firewall rules',
    status: 'active',
    capabilities: ['ssid', 'vlan', 'acl', 'firewall', 'switch', 'camera'],
    icon: 'Settings',
  },
  {
    id: 'workflow-creator',
    name: 'Workflow Creator',
    description: 'Creates automation workflows for network operations',
    status: 'active',
    capabilities: ['workflows', 'automation', 'alerts', 'scheduling'],
    icon: 'Workflow',
  },
];

export const useAgentStore = create<AgentState>((set, get) => ({
  agents: DEFAULT_AGENTS,
  activeAgentId: null,

  activeAgent: () => {
    const { agents, activeAgentId } = get();
    return agents.find((a) => a.id === activeAgentId);
  },

  setAgents: (agents) => set({ agents }),
  setActiveAgent: (id) => set({ activeAgentId: id }),
  updateAgentStatus: (id, status) =>
    set((state) => ({
      agents: state.agents.map((a) => (a.id === id ? { ...a, status } : a)),
    })),
}));
