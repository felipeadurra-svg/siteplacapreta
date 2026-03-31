import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Badge } from "@/components/ui/badge";
import { Eye, Download, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

// Mock data — will be replaced with real DB queries
const mockAvaliacoes = [
  { id: "AV-001", nome: "Carlos Silva", veiculo: "VW Fusca 1972", data: "2024-01-15", status: "aprovado" },
  { id: "AV-002", nome: "Ana Souza", veiculo: "Chevrolet Opala 1975", data: "2024-01-14", status: "pendente" },
  { id: "AV-003", nome: "Roberto Lima", veiculo: "Ford Maverick 1977", data: "2024-01-13", status: "aprovado" },
];

const Admin = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-16">
        <div className="container py-12 px-4">
          <div className="mb-8">
            <h1 className="font-heading text-3xl font-bold">
              Painel <span className="text-gradient-gold">Administrativo</span>
            </h1>
            <p className="text-muted-foreground mt-2">Gerencie todas as avaliações recebidas.</p>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
            {[
              { label: "Total de Avaliações", value: "3" },
              { label: "Pagamentos Aprovados", value: "2" },
              { label: "Pendentes", value: "1" },
            ].map(stat => (
              <div key={stat.label} className="bg-card border border-border rounded-xl p-5">
                <p className="text-sm text-muted-foreground">{stat.label}</p>
                <p className="font-heading text-2xl font-bold text-gradient-gold mt-1">{stat.value}</p>
              </div>
            ))}
          </div>

          {/* Search */}
          <div className="flex items-center gap-2 mb-6">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Buscar avaliação..." className="pl-9 bg-surface border-border" />
            </div>
          </div>

          {/* Table */}
          <div className="bg-card border border-border rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border bg-surface">
                    <th className="text-left py-3 px-4 text-muted-foreground font-medium">ID</th>
                    <th className="text-left py-3 px-4 text-muted-foreground font-medium">Proprietário</th>
                    <th className="text-left py-3 px-4 text-muted-foreground font-medium">Veículo</th>
                    <th className="text-left py-3 px-4 text-muted-foreground font-medium">Data</th>
                    <th className="text-left py-3 px-4 text-muted-foreground font-medium">Status</th>
                    <th className="text-right py-3 px-4 text-muted-foreground font-medium">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {mockAvaliacoes.map(av => (
                    <tr key={av.id} className="border-b border-border hover:bg-surface-hover transition-colors">
                      <td className="py-3 px-4 font-mono text-primary text-xs">{av.id}</td>
                      <td className="py-3 px-4">{av.nome}</td>
                      <td className="py-3 px-4 text-muted-foreground">{av.veiculo}</td>
                      <td className="py-3 px-4 text-muted-foreground">{av.data}</td>
                      <td className="py-3 px-4">
                        <Badge variant={av.status === "aprovado" ? "default" : "secondary"}
                          className={av.status === "aprovado" ? "bg-gradient-gold text-primary-foreground" : ""}>
                          {av.status === "aprovado" ? "Aprovado" : "Pendente"}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <Download className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Admin;
