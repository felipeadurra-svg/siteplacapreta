import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { ArrowRight, ArrowLeft, User, Car } from "lucide-react";

const estadosBrasil = [
  "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA",
  "PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"
];

export interface AvaliacaoFormData {
  nome: string;
  email: string;
  telefone: string;
  cidade: string;
  estado: string;
  marca: string;
  modelo: string;
  ano: string;
  placa: string;
  cor: string;
  motorizacao: string;
  observacoes: string;
}

interface VehicleFormProps {
  onSubmit: (data: AvaliacaoFormData) => void;
}

const VehicleForm = ({ onSubmit }: VehicleFormProps) => {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState<AvaliacaoFormData>({
    nome: "", email: "", telefone: "", cidade: "", estado: "",
    marca: "", modelo: "", ano: "", placa: "", cor: "", motorizacao: "", observacoes: "",
  });

  const update = (field: keyof AvaliacaoFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const step1Valid = formData.nome && formData.email && formData.telefone && formData.cidade && formData.estado;
  const step2Valid = formData.marca && formData.modelo && formData.ano && formData.placa && formData.cor;

  const handleSubmit = () => {
    if (step2Valid) onSubmit(formData);
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* Step indicator */}
      <div className="flex items-center justify-center gap-4 mb-10">
        <div className={`flex items-center gap-2 ${step >= 1 ? 'text-primary' : 'text-muted-foreground'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${step >= 1 ? 'bg-gradient-gold text-primary-foreground' : 'bg-secondary text-muted-foreground'}`}>
            1
          </div>
          <span className="text-sm font-medium hidden sm:inline">Proprietário</span>
        </div>
        <div className={`w-12 h-px ${step >= 2 ? 'bg-primary' : 'bg-border'}`} />
        <div className={`flex items-center gap-2 ${step >= 2 ? 'text-primary' : 'text-muted-foreground'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${step >= 2 ? 'bg-gradient-gold text-primary-foreground' : 'bg-secondary text-muted-foreground'}`}>
            2
          </div>
          <span className="text-sm font-medium hidden sm:inline">Veículo</span>
        </div>
      </div>

      {step === 1 && (
        <div className="space-y-6 animate-fade-in">
          <div className="flex items-center gap-2 mb-4">
            <User className="h-5 w-5 text-primary" />
            <h3 className="font-heading text-xl font-semibold">Dados do Proprietário</h3>
          </div>

          <div className="grid gap-4">
            <div>
              <Label htmlFor="nome" className="text-sm text-muted-foreground">Nome completo *</Label>
              <Input id="nome" value={formData.nome} onChange={e => update('nome', e.target.value)} className="mt-1 bg-surface border-border focus:border-primary" placeholder="Seu nome completo" />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="email" className="text-sm text-muted-foreground">Email *</Label>
                <Input id="email" type="email" value={formData.email} onChange={e => update('email', e.target.value)} className="mt-1 bg-surface border-border focus:border-primary" placeholder="seu@email.com" />
              </div>
              <div>
                <Label htmlFor="telefone" className="text-sm text-muted-foreground">Telefone *</Label>
                <Input id="telefone" value={formData.telefone} onChange={e => update('telefone', e.target.value)} className="mt-1 bg-surface border-border focus:border-primary" placeholder="(11) 99999-9999" />
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="cidade" className="text-sm text-muted-foreground">Cidade *</Label>
                <Input id="cidade" value={formData.cidade} onChange={e => update('cidade', e.target.value)} className="mt-1 bg-surface border-border focus:border-primary" placeholder="Sua cidade" />
              </div>
              <div>
                <Label htmlFor="estado" className="text-sm text-muted-foreground">Estado *</Label>
                <select id="estado" value={formData.estado} onChange={e => update('estado', e.target.value)} className="mt-1 flex h-10 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none">
                  <option value="">Selecione</option>
                  {estadosBrasil.map(uf => <option key={uf} value={uf}>{uf}</option>)}
                </select>
              </div>
            </div>
          </div>

          <div className="flex justify-end pt-4">
            <Button variant="gold" onClick={() => setStep(2)} disabled={!step1Valid}>
              Próximo <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-6 animate-fade-in">
          <div className="flex items-center gap-2 mb-4">
            <Car className="h-5 w-5 text-primary" />
            <h3 className="font-heading text-xl font-semibold">Dados do Veículo</h3>
          </div>

          <div className="grid gap-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="marca" className="text-sm text-muted-foreground">Marca *</Label>
                <Input id="marca" value={formData.marca} onChange={e => update('marca', e.target.value)} className="mt-1 bg-surface border-border focus:border-primary" placeholder="Ex: Volkswagen" />
              </div>
              <div>
                <Label htmlFor="modelo" className="text-sm text-muted-foreground">Modelo *</Label>
                <Input id="modelo" value={formData.modelo} onChange={e => update('modelo', e.target.value)} className="mt-1 bg-surface border-border focus:border-primary" placeholder="Ex: Fusca 1300" />
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <Label htmlFor="ano" className="text-sm text-muted-foreground">Ano *</Label>
                <Input id="ano" value={formData.ano} onChange={e => update('ano', e.target.value)} className="mt-1 bg-surface border-border focus:border-primary" placeholder="1972" />
              </div>
              <div>
                <Label htmlFor="placa" className="text-sm text-muted-foreground">Placa *</Label>
                <Input id="placa" value={formData.placa} onChange={e => update('placa', e.target.value)} className="mt-1 bg-surface border-border focus:border-primary" placeholder="ABC-1234" />
              </div>
              <div>
                <Label htmlFor="cor" className="text-sm text-muted-foreground">Cor *</Label>
                <Input id="cor" value={formData.cor} onChange={e => update('cor', e.target.value)} className="mt-1 bg-surface border-border focus:border-primary" placeholder="Azul" />
              </div>
            </div>
            <div>
              <Label htmlFor="motorizacao" className="text-sm text-muted-foreground">Motorização</Label>
              <Input id="motorizacao" value={formData.motorizacao} onChange={e => update('motorizacao', e.target.value)} className="mt-1 bg-surface border-border focus:border-primary" placeholder="Ex: 1.3 a ar" />
            </div>
            <div>
              <Label htmlFor="observacoes" className="text-sm text-muted-foreground">Observações</Label>
              <Textarea id="observacoes" value={formData.observacoes} onChange={e => update('observacoes', e.target.value)} className="mt-1 bg-surface border-border focus:border-primary min-h-[100px]" placeholder="Informações adicionais sobre o veículo..." />
            </div>
          </div>

          <div className="flex justify-between pt-4">
            <Button variant="goldOutline" onClick={() => setStep(1)}>
              <ArrowLeft className="mr-2 h-4 w-4" /> Voltar
            </Button>
            <Button variant="gold" onClick={handleSubmit} disabled={!step2Valid}>
              Próximo: Fotos <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default VehicleForm;
