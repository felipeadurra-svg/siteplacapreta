import { useState, useEffect } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import VehicleForm, { type AvaliacaoFormData } from "@/components/VehicleForm";
import PhotoUpload, { type PhotoData } from "@/components/PhotoUpload";
import { CheckCircle, CreditCard, ArrowLeft, Loader2, ExternalLink } from "lucide-react";
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

    try {
      const res = await fetch("https://siteplacapreta.onrender.com/avaliacao", {
        method: "POST",
        body: form,
      });
      if (!res.ok) throw new Error("Erro ao enviar avaliação");
      return await res.json();
    } catch (error) {
      console.error("Erro no upload:", error);
    }
  };

  const handlePayment = async () => {
    if (!window.MercadoPago) {
      alert("O sistema de pagamento ainda está carregando. Aguarde um segundo.");
      return;
    }

    setIsProcessing(true);

    try {
      // 1. Criar Preferência no Backend
      const prefRes = await fetch("https://siteplacapreta.onrender.com/create_preference", {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });
      
      const { id: preferenceId } = await prefRes.json();

      // 2. Inicializar SDK do Mercado Pago
      const mp = new window.MercadoPago('APP_USR-9c54b89f-6fec-46ec-bde6-e975a8f1d962', {
        locale: 'pt-BR'
      });

      // 3. Abrir o Checkout
      // O autoOpen: true pode ser bloqueado por pop-ups. 
      // Se não abrir, o usuário terá que clicar de novo.
      await mp.checkout({
        preference: { id: preferenceId },
        autoOpen: true,
      });

      // 4. Gerar o laudo em segundo plano
      const respostaLaudo = await enviarParaBackend();
      if (respostaLaudo?.id) {
        setLaudoId(respostaLaudo.id);
        // Só muda para a tela de sucesso se o laudo foi gerado e o checkout foi aberto
        setCurrentStep("success");
      }

    } catch (err) {
      console.error(err);
      alert("Erro ao processar. Verifique se o pop-up foi bloqueado.");
    } finally {
      setIsProcessing(false);
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
          
          {currentStep === "payment" && (
            <div className="max-w-md mx-auto p-6 bg-white rounded-xl shadow-lg border border-gray-200 animate-in fade-in slide-in-from-bottom-4">
              <div className="text-center space-y-4">
                <CreditCard className="h-10 w-10 mx-auto text-yellow-500" />
                <h2 className="text-2xl font-bold text-slate-900">Finalizar Avaliação</h2>
                <p className="text-slate-500 text-sm">Clique abaixo para abrir o pagamento seguro.</p>
                
                <div className="bg-slate-50 p-4 rounded-lg space-y-2 text-left border border-slate-100">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Serviço:</span>
                    <span className="font-medium text-slate-900 text-right">Laudo Técnico Placa Preta</span>
                  </div>
                  <div className="flex justify-between text-lg font-bold border-t border-slate-200 pt-2">
                    <span className="text-slate-900">Total:</span>
                    <span className="text-emerald-600">R$ 100,00</span>
                  </div>
                </div>

                <div className="flex flex-col gap-3 pt-4">
                  <Button 
                    className="w-full h-14 text-lg bg-yellow-500 hover:bg-yellow-600 text-black font-extrabold shadow-md transition-all active:scale-95"
                    onClick={handlePayment}
                    disabled={isProcessing}
                  >
                    {isProcessing ? (
                      <div className="flex items-center gap-2">
                        <Loader2 className="animate-spin h-5 w-5" />
                        <span>Abrindo Mercado Pago...</span>
                      </div>
                    ) : (
                      "PAGAR AGORA"
                    )}
                  </Button>
                  <Button variant="ghost" onClick={() => setCurrentStep("photos")} disabled={isProcessing} className="text-slate-500">
                    <ArrowLeft className="w-4 h-4 mr-2" /> Voltar
                  </Button>
                </div>
                <p className="text-[10px] text-slate-400 mt-4 italic">
                  * Certifique-se de permitir pop-ups neste site para abrir o checkout.
                </p>
              </div>
            </div>
          )}
          
          {currentStep === "success" && (
            <div className="text-center max-w-md mx-auto animate-in zoom-in duration-300">
              <div className="bg-emerald-50 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6 border border-emerald-100">
                <CheckCircle className="h-12 w-12 text-emerald-600" />
              </div>
              <h2 className="text-3xl font-bold mb-2 text-slate-900">Pagamento Iniciado!</h2>
              <p className="text-slate-600 mb-8">
                Assim que concluir o pagamento no Mercado Pago, seu laudo estará disponível abaixo.
              </p>
              <div className="space-y-4">
                <Button 
                  className="w-full bg-emerald-700 hover:bg-emerald-800 text-white h-14 text-lg font-bold shadow-lg flex items-center justify-center gap-2"
                  onClick={() => window.open(`https://siteplacapreta.onrender.com/cliente/${laudoId}`, '_blank')}
                >
                  <ExternalLink className="w-5 h-5" />
                  VER MEU LAUDO TÉCNICO
                </Button>
                <Link to="/" className="block">
                  <Button variant="outline" className="w-full">Voltar ao Início</Button>
                </Link>
              </div>
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Avaliacao;