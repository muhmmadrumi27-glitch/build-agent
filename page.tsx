"use client";

import { useState } from "react";
import {
  Plus,
  Play,
  Edit3,
  Trash2,
  Copy,
  Workflow,
  CheckCircle2,
  Clock,
  GitBranch,
  Save,
  X,
  GripVertical,
} from "lucide-react";
import toast from "react-hot-toast";

interface WorkflowStep {
  id: string;
  actionType: string;
  parameters: Record<string, any>;
  description: string;
}

interface Workflow {
  id: string;
  name: string;
  description: string;
  steps: WorkflowStep[];
  tags: string[];
  usageCount: number;
  successRate: number;
  createdAt: string;
}

const sampleWorkflows: Workflow[] = [
  {
    id: "1",
    name: "Daily Report Generation",
    description: "Generate daily analytics report from dashboard",
    steps: [
      { id: "s1", actionType: "browser_open", parameters: {}, description: "Open browser" },
      { id: "s2", actionType: "browser_navigate", parameters: { url: "https://analytics.example.com" }, description: "Navigate to analytics" },
      { id: "s3", actionType: "screenshot", parameters: {}, description: "Capture dashboard" },
    ],
    tags: ["daily", "report", "automated"],
    usageCount: 45,
    successRate: 0.98,
    createdAt: "2024-01-10T08:00:00Z",
  },
  {
    id: "2",
    name: "Social Media Posting",
    description: "Post content to multiple social platforms",
    steps: [
      { id: "s1", actionType: "browser_open", parameters: {}, description: "Open browser" },
      { id: "s2", actionType: "browser_navigate", parameters: { url: "https://twitter.com" }, description: "Go to Twitter" },
      { id: "s3", actionType: "browser_type", parameters: { selector: "textarea", text: "Hello world!" }, description: "Type post" },
    ],
    tags: ["social", "marketing"],
    usageCount: 23,
    successRate: 0.95,
    createdAt: "2024-01-12T10:00:00Z",
  },
];

const actionTypes = [
  "mouse_move", "mouse_click", "mouse_double_click", "mouse_right_click",
  "keyboard_type", "keyboard_shortcut", "scroll", "open_app", "close_app",
  "browser_open", "browser_navigate", "browser_click", "browser_type",
  "screenshot", "ocr", "vision_analyze", "wait",
];

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>(sampleWorkflows);
  const [showEditor, setShowEditor] = useState(false);
  const [editingWorkflow, setEditingWorkflow] = useState<Workflow | null>(null);

  const handleCreateWorkflow = () => {
    const newWorkflow: Workflow = {
      id: Date.now().toString(),
      name: "New Workflow",
      description: "",
      steps: [],
      tags: [],
      usageCount: 0,
      successRate: 0,
      createdAt: new Date().toISOString(),
    };
    setEditingWorkflow(newWorkflow);
    setShowEditor(true);
  };

  const handleSaveWorkflow = () => {
    if (!editingWorkflow) return;

    if (editingWorkflow.id && workflows.find((w) => w.id === editingWorkflow.id)) {
      setWorkflows(workflows.map((w) => (w.id === editingWorkflow.id ? editingWorkflow : w)));
    } else {
      setWorkflows([...workflows, editingWorkflow]);
    }
    setShowEditor(false);
    setEditingWorkflow(null);
    toast.success("Workflow saved");
  };

  const handleDeleteWorkflow = (id: string) => {
    setWorkflows(workflows.filter((w) => w.id !== id));
    toast.success("Workflow deleted");
  };

  const handleDuplicateWorkflow = (workflow: Workflow) => {
    const duplicated: Workflow = {
      ...workflow,
      id: Date.now().toString(),
      name: `${workflow.name} (Copy)`,
      usageCount: 0,
      createdAt: new Date().toISOString(),
    };
    setWorkflows([...workflows, duplicated]);
    toast.success("Workflow duplicated");
  };

  const addStep = () => {
    if (!editingWorkflow) return;
    const newStep: WorkflowStep = {
      id: Date.now().toString(),
      actionType: "screenshot",
      parameters: {},
      description: "New step",
    };
    setEditingWorkflow({
      ...editingWorkflow,
      steps: [...editingWorkflow.steps, newStep],
    });
  };

  const updateStep = (stepId: string, updates: Partial<WorkflowStep>) => {
    if (!editingWorkflow) return;
    setEditingWorkflow({
      ...editingWorkflow,
      steps: editingWorkflow.steps.map((s) => (s.id === stepId ? { ...s, ...updates } : s)),
    });
  };

  const removeStep = (stepId: string) => {
    if (!editingWorkflow) return;
    setEditingWorkflow({
      ...editingWorkflow,
      steps: editingWorkflow.steps.filter((s) => s.id !== stepId),
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Workflows</h1>
          <p className="text-gray-400 mt-1">Create and manage reusable automation workflows</p>
        </div>
        <button
          onClick={handleCreateWorkflow}
          className="flex items-center gap-2 px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Workflow
        </button>
      </div>

      {/* Workflow Editor */}
      {showEditor && editingWorkflow && (
        <div className="bg-dark-card rounded-xl border border-dark-border p-6 animate-fade-in">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-white">Workflow Editor</h3>
            <button
              onClick={() => setShowEditor(false)}
              className="p-1.5 rounded-lg text-gray-400 hover:bg-dark-border transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="space-y-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Name</label>
              <input
                type="text"
                value={editingWorkflow.name}
                onChange={(e) => setEditingWorkflow({ ...editingWorkflow, name: e.target.value })}
                className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Description</label>
              <textarea
                value={editingWorkflow.description}
                onChange={(e) => setEditingWorkflow({ ...editingWorkflow, description: e.target.value })}
                rows={2}
                className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Tags (comma separated)</label>
              <input
                type="text"
                value={editingWorkflow.tags.join(", ")}
                onChange={(e) => setEditingWorkflow({ ...editingWorkflow, tags: e.target.value.split(",").map((t) => t.trim()) })}
                className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-primary-500"
              />
            </div>
          </div>

          {/* Steps */}
          <div className="space-y-3 mb-6">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium text-white">Steps</h4>
              <button
                onClick={addStep}
                className="flex items-center gap-1 px-3 py-1.5 bg-dark-bg hover:bg-dark-border text-gray-300 rounded-lg transition-colors text-sm"
              >
                <Plus className="w-3 h-3" />
                Add Step
              </button>
            </div>

            {editingWorkflow.steps.map((step, index) => (
              <div key={step.id} className="flex items-start gap-3 p-3 bg-dark-bg rounded-lg">
                <div className="mt-2">
                  <GripVertical className="w-4 h-4 text-gray-500" />
                </div>
                <div className="flex-1 grid grid-cols-12 gap-3">
                  <div className="col-span-1">
                    <span className="text-xs text-gray-500">{index + 1}</span>
                  </div>
                  <div className="col-span-3">
                    <select
                      value={step.actionType}
                      onChange={(e) => updateStep(step.id, { actionType: e.target.value })}
                      className="w-full bg-dark-card border border-dark-border rounded px-2 py-1.5 text-sm text-white focus:outline-none focus:border-primary-500"
                    >
                      {actionTypes.map((type) => (
                        <option key={type} value={type}>{type}</option>
                      ))}
                    </select>
                  </div>
                  <div className="col-span-4">
                    <input
                      type="text"
                      value={step.description}
                      onChange={(e) => updateStep(step.id, { description: e.target.value })}
                      placeholder="Description"
                      className="w-full bg-dark-card border border-dark-border rounded px-2 py-1.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary-500"
                    />
                  </div>
                  <div className="col-span-3">
                    <input
                      type="text"
                      value={JSON.stringify(step.parameters)}
                      onChange={(e) => {
                        try {
                          const params = JSON.parse(e.target.value);
                          updateStep(step.id, { parameters: params });
                        } catch {}
                      }}
                      placeholder='{"key": "value"}'
                      className="w-full bg-dark-card border border-dark-border rounded px-2 py-1.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary-500"
                    />
                  </div>
                  <div className="col-span-1">
                    <button
                      onClick={() => removeStep(step.id)}
                      className="p-1.5 rounded text-gray-400 hover:text-red-400 hover:bg-red-500/20 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-end gap-3">
            <button
              onClick={() => setShowEditor(false)}
              className="px-4 py-2 bg-dark-bg hover:bg-dark-border text-gray-300 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSaveWorkflow}
              className="flex items-center gap-2 px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors"
            >
              <Save className="w-4 h-4" />
              Save Workflow
            </button>
          </div>
        </div>
      )}

      {/* Workflows Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {workflows.map((workflow) => (
          <div
            key={workflow.id}
            className="bg-dark-card rounded-xl border border-dark-border p-5 hover:border-gray-600 transition-colors"
          >
            <div className="flex items-start justify-between mb-3">
              <div className="p-2 bg-primary-500/20 rounded-lg">
                <Workflow className="w-5 h-5 text-primary-400" />
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => handleDuplicateWorkflow(workflow)}
                  className="p-1.5 rounded-lg text-gray-400 hover:bg-dark-border transition-colors"
                >
                  <Copy className="w-4 h-4" />
                </button>
                <button
                  onClick={() => {
                    setEditingWorkflow(workflow);
                    setShowEditor(true);
                  }}
                  className="p-1.5 rounded-lg text-gray-400 hover:bg-dark-border transition-colors"
                >
                  <Edit3 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleDeleteWorkflow(workflow.id)}
                  className="p-1.5 rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-500/20 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            <h3 className="text-lg font-semibold text-white mb-1">{workflow.name}</h3>
            <p className="text-sm text-gray-400 mb-4">{workflow.description}</p>

            <div className="flex flex-wrap gap-2 mb-4">
              {workflow.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-2 py-1 rounded-full bg-dark-bg text-xs text-gray-400"
                >
                  {tag}
                </span>
              ))}
            </div>

            <div className="flex items-center justify-between text-sm text-gray-400 mb-4">
              <div className="flex items-center gap-1">
                <CheckCircle2 className="w-4 h-4 text-green-400" />
                <span>{Math.round(workflow.successRate * 100)}% success</span>
              </div>
              <div className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                <span>{workflow.usageCount} runs</span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors text-sm">
                <Play className="w-4 h-4" />
                Run
              </button>
              <button className="flex items-center gap-2 px-3 py-2 bg-dark-bg hover:bg-dark-border text-gray-300 rounded-lg transition-colors text-sm">
                <GitBranch className="w-4 h-4" />
                {workflow.steps.length} steps
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
