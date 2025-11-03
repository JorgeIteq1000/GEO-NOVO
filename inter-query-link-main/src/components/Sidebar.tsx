// src/components/Sidebar.tsx
// (Arquivo ajustado, entregando completo conforme solicitado)

import {
  User,
  FileText,
  Award,
  AlertTriangle,
  ClipboardList,
  Archive,
  School,
  DollarSign,
  BarChart3,
  Settings, // <-- 1. IMPORTAR O NOVO ÍCONE
} from "lucide-react";

interface SidebarProps {
  activeSection: string;
  onSectionChange: (section: string) => void;
}

const navigationItems = [
  { id: "Pessoa", label: "Pessoa", icon: User },
  { id: "Documento", label: "Documento", icon: FileText },
  { id: "Certificado", label: "Certificado", icon: Award },
  { id: "Ocorrência", label: "Ocorrência", icon: AlertTriangle },
  { id: "Nota/Falta", label: "Nota/Falta", icon: ClipboardList },
  { id: "Requerimento", label: "Requerimento", icon: Archive },
  { id: "Matrícula", label: "Matrícula", icon: School },
  { id: "Financeiro", label: "Financeiro", icon: DollarSign },
  { id: "Relatórios", label: "Relatórios", icon: BarChart3 },
  // 2. ADICIONAR O NOVO ITEM ABAIXO
  { id: "Configuracoes", label: "Configurações", icon: Settings },
];

export default function Sidebar({
  activeSection,
  onSectionChange,
}: SidebarProps) {
  return (
    <aside className="w-64 bg-[hsl(var(--sidebar-background))] text-[hsl(var(--sidebar-foreground))] flex flex-col fixed left-0 top-0 h-screen">
      <div className="p-6 border-b border-[hsl(var(--sidebar-border))]">
        <h1 className="text-xl font-bold text-[hsl(var(--sidebar-primary-foreground))]">
          Sistema de Consulta
        </h1>
      </div>

      <nav className="flex-1 overflow-y-auto py-4">
        <ul className="space-y-1 px-3">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeSection === item.id;

            return (
              <li key={item.id}>
                <button
                  onClick={() => onSectionChange(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-smooth ${
                    isActive
                      ? "bg-[hsl(var(--sidebar-primary))] text-[hsl(var(--sidebar-primary-foreground))]"
                      : "hover:bg-[hsl(var(--sidebar-accent))] text-[hsl(var(--sidebar-foreground))]"
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  <span className="font-medium">{item.label}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </nav>
    </aside>
  );
}
