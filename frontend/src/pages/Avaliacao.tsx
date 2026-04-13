import { useState, useEffect } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import VehicleForm, { type AvaliacaoFormData } from "@/components/VehicleForm";
import PhotoUpload, { type PhotoData } from "@/components/PhotoUpload";
import { CheckCircle, CreditCard, ArrowLeft, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

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
      alert("Sistema carregando...");
      return;
    }

    setIsProcessing(true);

    try {
      const prefRes = await fetch("https://siteplacapreta.onrender.com/create_preference", {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });
      
      const { id: preferenceId } = await prefRes.json();

      const mp = new window.MercadoPago('APP_USR-9c54b89f-6fec-46ec-bde6-e975a8f1d962', {
        locale: 'pt-BR'
      });

      mp.checkout({
        preference: { id: preferenceId },
        autoOpen: true,
      });

      const respostaLaudo = await enviarParaBackend();
      if (respostaLaudo?.id) {
        setLaudoId(respostaLaudo.id);
      }

      setTimeout(() => {
        setIsProcessing(false);
        setCurrentStep("success");
      }, 3000);

    } catch (err) {
      console.error(err);
      setIsProcessing(false);
      alert("Erro ao iniciar pagamento.");
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
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
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

          {currentStep === "form" && <VehicleForm onSubmit={handleFormSubmit} />}
          {currentStep === "photos" && <PhotoUpload onSubmit={handlePhotosSubmit} onBack={() => setCurrentStep("form")} />}
          
          {/* TELA DE PAGAMENTO USANDO DIVS NORMAIS (EVITA ERRO DE BUILD NO VERCEL) */}
          {currentStep === "payment" && (
            <div className="max-w-md mx-auto p-6 bg-white rounded-xl shadow-lg border border-gray-200 animate-in fade-in slide-in-from-bottom-4">
              <div className="text-center space-y-4">
                <CreditCard className="h-10 w-10 mx-auto text-yellow-500" />
                <h2 className="text-2xl font-bold">Finalizar Avaliação</h2>
                <p className="text-gray-500 text-sm">Pagamento seguro via Mercado Pago.</p>
                
                <div className="bg-gray-50 p-4 rounded-lg space-y-2 text-left">
                  <div className="flex justify-between text-sm">
                    <span>Serviço:</span>
                    <span className="font-medium text-right">Laudo Placa Preta</span>
                  </div>
                  <div className="flex justify-between text-lg font-bold border-t pt-2">
                    <span>Total:</span>
                    <span className="text-green-600">R$ 100,00</span>
                  </div>
                </div>

                <div className="flex flex-col gap-3 pt-4">
                  <Button 
                    className="w-full h-12 text-lg bg-yellow-500 hover:bg-yellow-600 text-black font-bold"
                    onClick={handlePayment}
                    disabled={isProcessing}
                  >
                    {isProcessing ? <Loader2 className="animate-spin" /> : "Pagar Agora"}
                  </Button>
                  <Button variant="ghost" onClick={() => setCurrentStep("photos")} disabled={isProcessing}>
                    Voltar
                  </Button>
                </div>
              </div>
            </div>
          )}
          
          {currentStep === "success" && (
            <div className="text-center max-w-md mx-auto">
              <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
              <h2 className="text-3xl font-bold mb-2">Concluído!</h2>
              <p className="text-muted-foreground mb-6">Seu laudo foi gerado com sucesso.</p>
              <Button 
                className="w-full bg-green-700 hover:bg-green-800 text-white h-12"
                onClick={() => window.open(`https://siteplacapreta.onrender.com/cliente/${laudoId}`, '_blank')}
              >
                Ver Laudo Técnico
              </Button>
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Avaliacao;