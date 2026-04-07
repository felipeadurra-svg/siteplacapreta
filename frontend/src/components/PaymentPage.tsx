import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { CreditCard, Shield, CheckCircle, QrCode } from "lucide-react";

interface PaymentPageProps {
  onPaymentConfirm: () => void;
  onBack: () => void;
  isProcessing: boolean;
}

const PaymentPage = ({
  onPaymentConfirm,
  onBack,
  isProcessing,
}: PaymentPageProps) => {
  const [timeLeft, setTimeLeft] = useState(15 * 60);
  const [copied, setCopied] = useState(false);

  // 🔥 SEU PIX REAL (COPIA E COLA)
  const pixCode =
    "00020126440014br.gov.bcb.pix0122felipeadurra@yahoo.com520400005303986540597.005802BR5921Regina Lima de Arruda6009Sao Paulo62240520daqr32365891044901696304A7AF";

  useEffect(() => {
    const interval = setInterval(() => {
      setTimeLeft((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const r = s % 60;
    return `${m.toString().padStart(2, "0")}:${r
      .toString()
      .padStart(2, "0")}`;
  };

  const copyPix = async () => {
    await navigator.clipboard.writeText(pixCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="max-w-lg mx-auto text-center">

      {/* ÍCONE */}
      <div className="flex items-center justify-center w-16 h-16 rounded-full bg-gradient-gold mx-auto mb-6">
        <CreditCard className="h-7 w-7 text-primary-foreground" />
      </div>

      {/* TÍTULO */}
      <h3 className="font-heading text-2xl font-bold mb-2">
        Pagamento da Avaliação
      </h3>

      <p className="text-muted-foreground mb-8">
        Confirme o pagamento para iniciar a análise do seu veículo.
      </p>

      {/* CARD PRINCIPAL */}
      <div className="bg-card border border-border rounded-xl p-6 mb-8">
        <div className="flex justify-between items-center mb-4">
          <span className="text-muted-foreground">
            Avaliação Técnica Placa Preta
          </span>
          <span className="font-heading text-2xl font-bold text-gradient-gold">
            R$ 97,00
          </span>
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

      {/* 🔥 CARD PIX */}
      <div className="bg-card border border-border rounded-xl p-6 mb-6">

        <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground mb-3">
          <QrCode className="h-4 w-4" />
          Pagamento via Pix
        </div>

        <div className="font-heading text-lg mb-4 text-primary">
          Expira em {formatTime(timeLeft)}
        </div>

        {/* QR CODE */}
        <div className="flex justify-center mb-4">
          <div className="p-3 bg-white rounded-lg">
            <img
              src="/qrcode-pix.png"
              className="w-44 h-44"
              alt="QR Code Pix"
            />
          </div>
        </div>

        {/* 🔥 COPIA E COLA */}
        <div className="mt-4">
          <p className="text-xs text-muted-foreground mb-2">
            Pix copia e cola:
          </p>

          <div className="flex items-center gap-2">
            <input
              value={pixCode}
              readOnly
              className="flex-1 p-2 text-xs border rounded bg-muted"
            />

            <button
              onClick={copyPix}
              className="px-3 py-2 text-xs bg-primary text-white rounded"
            >
              {copied ? "Copiado!" : "Copiar"}
            </button>
          </div>
        </div>

        <p className="text-xs text-muted-foreground mt-3">
          Escaneie ou copie o código para pagar no app do seu banco
        </p>
      </div>

      {/* BOTÕES */}
      <Button
        variant="gold"
        size="lg"
        className="w-full text-base py-6 mb-4"
        onClick={onPaymentConfirm}
        disabled={isProcessing}
      >
        {isProcessing ? "Processando..." : "Confirmar Pagamento"}
      </Button>

      <Button
        variant="ghost"
        onClick={onBack}
        className="text-muted-foreground"
      >
        Voltar
      </Button>

      {/* SEGURANÇA */}
      <div className="flex items-center justify-center gap-2 mt-6 text-xs text-muted-foreground">
        <Shield className="h-3 w-3" />
        Pagamento seguro e protegido
      </div>
    </div>
  );
};

export default PaymentPage;