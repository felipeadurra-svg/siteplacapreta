import { Button } from "@/components/ui/button";
import { CreditCard, Shield, CheckCircle } from "lucide-react";

interface PaymentPageProps {
  onPaymentConfirm: () => void;
  onBack: () => void;
  isProcessing: boolean;
}

const PaymentPage = ({ onPaymentConfirm, onBack, isProcessing }: PaymentPageProps) => {
  return (
    <div className="max-w-lg mx-auto text-center">
      <div className="flex items-center justify-center w-16 h-16 rounded-full bg-gradient-gold mx-auto mb-6">
        <CreditCard className="h-7 w-7 text-primary-foreground" />
      </div>

      <h3 className="font-heading text-2xl font-bold mb-2">Pagamento da Avaliação</h3>
      <p className="text-muted-foreground mb-8">
        Confirme o pagamento para iniciar a análise do seu veículo.
      </p>

      <div className="bg-card border border-border rounded-xl p-6 mb-8">
        <div className="flex justify-between items-center mb-4">
          <span className="text-muted-foreground">Avaliação Técnica Placa Preta</span>
          <span className="font-heading text-2xl font-bold text-gradient-gold">R$ 197,00</span>
        </div>
        <div className="border-t border-border pt-4 space-y-2">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <CheckCircle className="h-4 w-4 text-primary" />
            <span>Relatório técnico completo em PDF</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <CheckCircle className="h-4 w-4 text-primary" />
            <span>Análise por IA de todas as fotos</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <CheckCircle className="h-4 w-4 text-primary" />
            <span>Envio por email automático</span>
          </div>
        </div>
      </div>

      <Button
        variant="gold"
        size="lg"
        className="w-full text-base py-6 mb-4"
        onClick={onPaymentConfirm}
        disabled={isProcessing}
      >
        {isProcessing ? "Processando..." : "Confirmar Pagamento"}
      </Button>

      <Button variant="ghost" onClick={onBack} className="text-muted-foreground">
        Voltar
      </Button>

      <div className="flex items-center justify-center gap-2 mt-6 text-xs text-muted-foreground">
        <Shield className="h-3 w-3" />
        Pagamento seguro e protegido
      </div>
    </div>
  );
};

export default PaymentPage;
