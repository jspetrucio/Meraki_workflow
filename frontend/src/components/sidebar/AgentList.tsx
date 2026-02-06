import { useState } from 'react';
import { useAgentStore } from '@/stores/agentStore';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { Search, Settings, Workflow, Zap } from 'lucide-react';

const AGENT_ICONS = {
  'Search': Search,
  'Settings': Settings,
  'Workflow': Workflow,
};

export function AgentList() {
  const { agents, activeAgentId, setActiveAgent } = useAgentStore();
  const [autoRouting, setAutoRouting] = useState(true);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-500';
      case 'busy':
        return 'bg-yellow-500';
      case 'inactive':
        return 'bg-gray-400';
      default:
        return 'bg-gray-400';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'active':
        return 'Active';
      case 'busy':
        return 'Busy';
      case 'inactive':
        return 'Inactive';
      default:
        return 'Unknown';
    }
  };

  const toggleAutoRouting = () => {
    const newValue = !autoRouting;
    setAutoRouting(newValue);
    if (newValue) {
      setActiveAgent(null); // Clear manual selection when enabling auto-routing
    }
  };

  return (
    <div className="p-2 space-y-2">
      <div className="flex items-center justify-between px-2">
        <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          Agents
        </div>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant={autoRouting ? "default" : "outline"}
                size="sm"
                onClick={toggleAutoRouting}
                className="h-6 px-2"
              >
                <Zap className="h-3 w-3" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>{autoRouting ? 'Auto-routing enabled' : 'Manual agent selection'}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      <TooltipProvider>
        <div className="space-y-1">
          {agents.map((agent) => {
            const IconComponent = AGENT_ICONS[agent.icon as keyof typeof AGENT_ICONS] || Search;
            const isActive = agent.id === activeAgentId;

            return (
              <Tooltip key={agent.id}>
                <TooltipTrigger asChild>
                  <button
                    onClick={() => setActiveAgent(isActive ? null : agent.id)}
                    className={`
                      w-full flex items-center gap-2 p-2 rounded-md
                      transition-colors hover:bg-muted
                      ${isActive ? 'bg-muted border border-primary' : ''}
                    `}
                    aria-label={`${agent.name}: ${agent.description}`}
                  >
                    <div className="relative">
                      <IconComponent className="h-4 w-4 text-muted-foreground" />
                      <span
                        className={`
                          absolute -bottom-0.5 -right-0.5 h-2 w-2 rounded-full
                          ${getStatusColor(agent.status)}
                        `}
                        aria-label={getStatusLabel(agent.status)}
                      />
                    </div>

                    <div className="flex-1 min-w-0 text-left">
                      <div className="text-xs font-medium truncate">
                        {agent.name}
                      </div>
                    </div>

                    {isActive && (
                      <Badge variant="secondary" className="text-xs px-1 py-0">
                        Active
                      </Badge>
                    )}
                  </button>
                </TooltipTrigger>
                <TooltipContent side="right">
                  <div className="space-y-1">
                    <p className="font-semibold">{agent.name}</p>
                    <p className="text-xs">{agent.description}</p>
                    <p className="text-xs text-muted-foreground">
                      Status: {getStatusLabel(agent.status)}
                    </p>
                  </div>
                </TooltipContent>
              </Tooltip>
            );
          })}
        </div>
      </TooltipProvider>
    </div>
  );
}
