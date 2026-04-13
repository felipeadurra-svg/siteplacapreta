import { useState, useEffect } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import VehicleForm, { type AvaliacaoFormData } from "@/components/VehicleForm";
import PhotoUpload, { type PhotoData } from "@/components/PhotoUpload";
import { CheckCircle, CreditCard, ArrowLeft, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type Step = "form" | "photos" | "payment" | "success";

declare global {
  interface Window {
    MercadoPago: any;
  }
}

const Avaliacao = () => {
  const [currentStep, setCurrentStep] = useState<Step>("form");
  const [formData, setFormData] = useState<AvaliacaoFormData | null>(null);
  const [photos, setPhotos] = useState<PhotoData>({});
  const [isProcessing, setIsProcessing] = useState(false);
  const [laudoId, setLaudoId] = useState<string | null>(null);

  const steps = ["Dados", "Fotos", "Pagamento", "Concluído"];
  const stepIndex: Record<Step, number> = { form: 0, photos: 1, payment: 2, success: 3 };

  useEffect(() => {
    if (document.getElementById("mp-sdk")) return;
    const script = document.createElement("script");
    script.id = "mp-sdk";
    script.src = "https://sdk.mercadopago.com/js/v2";
    script.async = true;
    document.body.appendChild(script);
  }, []);

  const handleFormSubmit = (data: AvaliacaoFormData) => {
    setFormData(data);
    setCurrentStep("photos");
  };

  const handlePhotosSubmit = (photoData: PhotoData) => {
    setPhotos(photoData);
    setCurrentStep("payment");
  };

  const enviarParaBackend = async () => {
    if (!formData) return;
    const form = new FormData();
    form.append("nome", formData.nome);
    form.append("marca", formData.marca);
    form.append("modelo", formData.modelo);
    form.append("ano", formData.ano);

    Object.entries(photos).forEach(([key, file]) => {
      if (file instanceof File) {
        form.append(`foto_${key}`, file);
      }
    });

    const res = await fetch("https://siteplacapreta.onrender.com/avaliacao", {
      method: "POST",
      body: form,
    });

    if (!res.ok) throw new Error("Erro ao enviar avaliação");
    return await res.json();
  };

  const handlePayment = async () => {
    if (!window.MercadoPago) {
      alert("O sistema de pagamento está carregando. Tente novamente em instantes.");
      return;
    }

    setIsProcessing(true);

    try {
      // 1. Chama seu novo Payment.py através da rota do backend
      const prefRes = await fetch("https://siteplacapreta.onrender.com/create_preference", {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });
      
      const { id: preferenceId } = await prefRes.json();

      // 2. Inicializa o checkout com sua chave pública
      const mp = new window.MercadoPago('APP_USR-9c54b89f-6fec-46ec-bde6-e975a8f1d962', {
        locale: 'pt-BR'
      });

      mp.checkout({
        preference: { id: preferenceId },
        autoOpen: true,
      });

      // 3. Processa a geração do laudo enquanto o usuário paga
      const respostaLaudo = await enviarParaBackend();
      if (respostaLaudo?.id) {
        setLaudoId(respostaLaudo.id);
      }

      // Simula tempo de finalização
      setTimeout(() => {
        setIsProcessing(false);
        setCurrentStep("success");
      }, 3000);

    } catch (err) {
      console.error(err);
      setIsProcessing(false);
      alert("Houve um problema ao iniciar o pagamento.");
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-16">
        <div className="container py-12 px-4 max-w-4xl mx-auto">
          {/* STEPPER */}
          <div className="flex items-center justify-center gap-4 mb-12">
            {steps.map((label, i) => (
              <div key={label} className="flex items-center gap-2">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
                  stepIndex[currentStep] >= i ? "bg-yellow-500 text-black" : "bg-muted text-muted-foreground"
                }`}>
                  {i + 1}
                </div>
                <span className={`text-xs hidden md:inline ${stepIndex[currentStep] === i ? "font-bold" : ""}`}>
                  {label}
                </span>
              </div>
            ))}
          </div>

          {/* FORMULÁRIO */}
          {currentStep === "form" && <VehicleForm onSubmit={handleFormSubmit} />}
          
          {/* UPLOAD DE FOTOS */}
          {currentStep === "photos" && (
            <PhotoUpload onSubmit={handlePhotosSubmit} onBack={() => setCurrentStep("form")} />
          )}
          
          {/* TELA DE PAGAMENTO INTEGRADA */}
          {currentStep === "payment" && (
            <div className="max-w-md mx-auto animate-in fade-in slide-in-from-bottom-4 duration-500">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CreditCard className="h-5 w-5" />
                    Finalizar Avaliação
                  </CardTitle>
                  <CardDescription>
                    Pague com segurança via Mercado Pago para gerar seu laudo técnico.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="bg-muted p-4 rounded-lg space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Serviço:</span>
                      <span className="font-medium">Laudo Técnico Placa Preta</span>
                    </div>
                    <div className="flex justify-between text-lg font-bold border-t pt-2">
                      <span>Total:</span>
                      <span className="text-green-600">R$ 100,00</span>
                    </div>
                  </div>

                  <div className="flex flex-col gap-3">
                    <Button 
                      className="w-full h-12 text-lg bg-yellow-500 hover:bg-yellow-600 text-black font-bold"
                      onClick={handlePayment}
                      disabled={isProcessing}
                    >
                      {isProcessing ? (
                        <>
                          <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                          Processando...
                        </>
                      ) : (
                        "Pagar com Mercado Pago"
                      )}
                    </Button>
                    <Button 
                      variant="outline" 
                      onClick={() => setCurrentStep("photos")}
                      disabled={isProcessing}
                    >
                      <ArrowLeft className="mr-2 h-4 w-4" />
                      Voltar para Fotos
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
          
          {/* SUCESSO */}
          {currentStep === "success" && (
            <div className="text-center animate-in zoom-in duration-500 max-w-md mx-auto">
              <div className="bg-green-100 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
                <CheckCircle className="h-12 w-12 text-green-600" />
              </div>
              <h2 className="text