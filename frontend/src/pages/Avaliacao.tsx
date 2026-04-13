import { useState, useEffect } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import VehicleForm, { type AvaliacaoFormData } from "@/components/VehicleForm";
import PhotoUpload, { type PhotoData } from "@/components/PhotoUpload";
import { CheckCircle, CreditCard, ArrowLeft, Loader2, ExternalLink, ShieldCheck } from "lucide-react";
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
      return null;
    }
  };

  const handlePayment = async () => {
    if (!window.MercadoPago) {
      alert("O sistema de pagamento ainda está carregando. Por favor, aguarde.");
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

      // 2. Inicializar SDK
      const mp = new window.MercadoPago('APP_USR-9c54b89f-6fec-46ec-bde6-e975a8f1d962', {
        locale: 'pt-BR'
      });

      // 3. Tentar abrir o Checkout
      // Importante: autoOpen costuma ser bloqueado por pop-ups no primeiro clique
      mp.checkout({
        preference: { id: preferenceId },
        autoOpen: true,
      });

      // 4. Aguardar um pouco para garantir que o modal iniciou antes de mudar a tela
      setTimeout(async () => {
        const respostaLaudo = await enviarParaBackend();
        if (respostaLaudo?.id) {
          setLaudoId(respostaLaudo.id);
          setCurrentStep("success");
        }
        setIsProcessing(false);
      }, 1500);

    } catch (err) {
      console.error(err);
      setIsProcessing(false);
      alert("Houve um erro ao processar. Verifique se o navegador bloqueou o pop-up.");
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
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                  stepIndex[currentStep] >= i ? "bg-yellow-500 text-black scale-110" : "bg-muted text-muted-foreground"
                }`}>
                  {i + 1}
                </div>
                <span className={`text-xs hidden md:inline ${stepIndex[currentStep] === i ? "font-bold text-yellow-600" : "text-muted-foreground"}`}>
                  {label}
                </span>
              </div>
            ))}
          </div>

          {currentStep === "form" && <VehicleForm onSubmit={handleFormSubmit} />}
          {currentStep === "photos" && <PhotoUpload onSubmit={handlePhotosSubmit} onBack={() => setCurrentStep("form")} />}
          
          {currentStep === "payment" && (
            <div className="max-w-md mx-auto p-8 bg-white rounded-2xl shadow-xl border border-slate-200 animate-in fade-in slide-in-from-bottom-6">
              <div className="text-center space-y-6">
                <div className="bg-yellow-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto">
                  <CreditCard className="h-8 w-8 text-yellow-600" />
                </div>
                
                <div className="space-y-2">
                  <h2 className="text-2xl font-black text-slate-900">Finalizar Pagamento</h2>
                  <p className="text-slate-500 text-sm">O checkout será aberto em uma nova janela.</p>
                </div>
                
                <div className="bg-slate-50 p-5 rounded-xl space-y-3 text-left border border-slate-100">
                  <div className="flex justify-between text-sm text-slate-600">
                    <span>Serviço:</span>
                    <span className="font-semibold text-slate-900">Laudo Placa Preta</span>
                  </div>
                  <div className="flex justify-between text-xl font-bold border-t border-slate-200 pt-3 text-slate-900">
                    <span>Total:</span>
                    <span className="text-emerald-600">R$ 100,00</span>
                  </div>
                </div>

                <div className="flex flex-col gap-4 pt-2">
                  <Button 
                    className="w-full h-14 text-lg bg-yellow-500 hover:bg-yellow-600 text-black font-black shadow-lg transition-transform active:scale-95"
                    onClick={handlePayment}
                    disabled={isProcessing}
                  >
                    {isProcessing ? (
                      <div className="flex items-center gap-2">
                        <Loader2 className="animate-spin h-5 w-5" />
                        <span>PROCESSANDO...</span>
                      </div>
                    ) : (
                      "PAGAR COM MERCADO PAGO"
                    )}
                  </Button>
                  
                  <Button variant="ghost" onClick={() => setCurrentStep("photos")} disabled={isProcessing} className="text-slate-400">
                    <ArrowLeft className="w-4 h-4 mr-2" /> Voltar para fotos
                  </Button>
                </div>

                <div className="flex items-center justify-center gap-2 text-[10px] text-slate-400 uppercase tracking-widest font-bold">
                  <ShieldCheck className="w-3 h-3 text-emerald-500" />
                  Pagamento 100% Seguro
                </div>
              </div>
            </div>
          )}
          
          {currentStep === "success" && (
            <div className="text-center max-w-md mx-auto animate-in zoom-in-95 duration-500">
              <div className="bg-emerald-50 w-24 h-24 rounded-full flex items-center justify-center mx-auto mb-8 border-4 border-white shadow-md">
                <CheckCircle className="h-14 w-14 text-emerald-500" />
              </div>
              <h2 className="text-3xl font-black mb-3 text-slate-900">Tudo Pronto!</h2>
              <p className="text-slate-600 mb-10 leading-relaxed">
                Seu pagamento foi iniciado. Clique no botão abaixo para acessar o laudo técnico gerado pela nossa inteligência pericial.
              </p>
              
              <div className="space-y-4">
                <Button 
                  className="w-full bg-slate-900 hover:bg-black text-white h-16 text-lg font-bold shadow-xl flex items-center justify-center gap-3 transition-all hover:translate-y-[-2px]"
                  onClick={() => window.open(`https://siteplacapreta.onrender.com/cliente/${laudoId}`, '_blank')}
                >
                  <ExternalLink className="w-5 h-5" />
                  ACESSAR LAUDO TÉCNICO
                </Button>
                
                <Link to="/" className="block">
                  <Button variant="outline" className="w-full h-12 border-slate-200 text-slate-500">
                    Sair e Voltar ao Início
                  </Button>
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