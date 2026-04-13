import { useState, useEffect } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import VehicleForm, { type AvaliacaoFormData } from "@/components/VehicleForm";
import PhotoUpload, { type PhotoData } from "@/components/PhotoUpload";
import { CheckCircle, CreditCard, ArrowLeft, Loader2, ExternalLink, ShieldCheck, AlertCircle } from "lucide-react";
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
  const [preferenceId, setPreferenceId] = useState<string | null>(null);
  const [errorLoadingPayment, setErrorLoadingPayment] = useState(false);

  const steps = ["Dados", "Fotos", "Pagamento", "Concluído"];
  const stepIndex: Record<Step, number> = { form: 0, photos: 1, payment: 2, success: 3 };

  // Carrega o SDK do Mercado Pago
  useEffect(() => {
    if (document.getElementById("mp-sdk")) return;
    const script = document.createElement("script");
    script.id = "mp-sdk";
    script.src = "https://sdk.mercadopago.com/js/v2";
    script.async = true;
    document.body.appendChild(script);
  }, []);

  // Busca a preferência de pagamento assim que entrar na etapa de pagamento
  useEffect(() => {
    if (currentStep === "payment" && !preferenceId) {
      const fetchPreference = async () => {
        try {
          setErrorLoadingPayment(false);
          const prefRes = await fetch("https://siteplacapreta.onrender.com/create_preference", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
          });
          
          if (!prefRes.ok) throw new Error("Erro no servidor");
          
          const data = await prefRes.json();
          if (data.id) {
            setPreferenceId(data.id);
          } else {
            throw new Error("ID de preferência não retornado");
          }
        } catch (err) {
          console.error("Erro ao carregar pagamento:", err);
          setErrorLoadingPayment(true);
        }
      };
      fetchPreference();
    }
  }, [currentStep, preferenceId]);

  const handleFormSubmit = (data: AvaliacaoFormData) => {
    setFormData(data);
    setCurrentStep("photos");
  };

  const handlePhotosSubmit = (photoData: PhotoData) => {
    setPhotos(photoData);
    setCurrentStep("payment");
  };

  const handlePaymentAndGenerate = async () => {
    if (!window.MercadoPago || !preferenceId) return;

    setIsProcessing(true);

    try {
      // 1. Inicializa o MP
      const mp = new window.MercadoPago('APP_USR-9c54b89f-6fec-46ec-bde6-e975a8f1d962', {
        locale: 'pt-BR'
      });

      // 2. Abre o Checkout
      mp.checkout({
        preference: { id: preferenceId },
        autoOpen: true,
      });

      // 3. Envia os dados para gerar o laudo
      const form = new FormData();
      if (formData) {
        form.append("nome", formData.nome);
        form.append("marca", formData.marca);
        form.append("modelo", formData.modelo);
        form.append("ano", formData.ano);
      }

      Object.entries(photos).forEach(([key, file]) => {
        if (file instanceof File) form.append(`foto_${key}`, file);
      });

      const res = await fetch("https://siteplacapreta.onrender.com/avaliacao", {
        method: "POST",
        body: form,
      });

      const respostaLaudo = await res.json();
      
      if (respostaLaudo?.id) {
        setLaudoId(respostaLaudo.id);
        // Pequeno delay para garantir que o usuário viu o modal abrir
        setTimeout(() => {
            setCurrentStep("success");
            setIsProcessing(false);
        }, 2500);
      }

    } catch (err) {
      console.error(err);
      setIsProcessing(false);
      alert("Erro ao processar. Verifique se o pop-up foi bloqueado pelo navegador.");
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
                  stepIndex[currentStep] >= i ? "bg-yellow-500 text-black shadow-md scale-110" : "bg-muted text-muted-foreground"
                }`}>
                  {i + 1}
                </div>
                <span className={`text-xs hidden md:inline ${stepIndex[currentStep] === i ? "font-bold text-slate-900" : "text-muted-foreground"}`}>
                  {label}
                </span>
              </div>
            ))}
          </div>

          {currentStep === "form" && <VehicleForm onSubmit={handleFormSubmit} />}
          {currentStep === "photos" && <PhotoUpload onSubmit={handlePhotosSubmit} onBack={() => setCurrentStep("form")} />}
          
          {currentStep === "payment" && (
            <div className="max-w-md mx-auto p-8 bg-white rounded-2xl shadow-2xl border border-slate-100 animate-in fade-in slide-in-from-bottom-4">
              <div className="text-center space-y-6">
                <div className="bg-yellow-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto">
                  <CreditCard className="h-8 w-8 text-yellow-500" />
                </div>
                <div className="space-y-2">
                  <h2 className="text-2xl font-black text-slate-900">CHECKOUT SEGURO</h2>
                  <p className="text-slate-500 text-sm">Pague e gere seu laudo técnico instantaneamente.</p>
                </div>
                
                <div className="bg-slate-50 p-6 rounded-xl border border-slate-100 text-left">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-slate-600">Serviço:</span>
                    <span className="text-sm font-bold text-slate-900 text-right">Laudo Pericial IA</span>
                  </div>
                  <div className="flex justify-between items-center mt-3 border-t border-slate-200 pt-3">
                    <span className="text-slate-900 font-bold">Total:</span>
                    <span className="text-2xl font-black text-emerald-600">R$ 100,00</span>
                  </div>
                </div>

                {errorLoadingPayment && (
                  <div className="flex items-center gap-2 p-3 bg-red-50 text-red-600 rounded-lg text-xs font-medium">
                    <AlertCircle className="h-4 w-4" />
                    Erro ao conectar com o servidor de pagamento. 
                    <button onClick={() => setPreferenceId(null)} className="underline ml-1">Tentar novamente</button>
                  </div>
                )}

                <div className="flex flex-col gap-4">
                  <Button 
                    className="w-full h-16 text-lg bg-yellow-500 hover:bg-yellow-600 text-black font-black rounded-xl shadow-lg transition-all active:scale-95 disabled:opacity-50 disabled:bg-slate-200"
                    onClick={handlePaymentAndGenerate}
                    disabled={isProcessing || !preferenceId}
                  >
                    {isProcessing ? (
                      <div className="flex items-center gap-3">
                        <Loader2 className="animate-spin h-6 w-6" />
                        <span>PROCESSANDO...</span>
                      </div>
                    ) : !preferenceId && !errorLoadingPayment ? (
                      <div className="flex items-center gap-2">
                        <Loader2 className="animate-spin h-4 w-4" />
                        <span>CARREGANDO PAGAMENTO...</span>
                      </div>
                    ) : (
                      "PAGAR AGORA"
                    )}
                  </Button>
                  
                  <Button variant="ghost" onClick={() => setCurrentStep("photos")} disabled={isProcessing} className="text-slate-400 text-xs uppercase tracking-tighter">
                    <ArrowLeft className="w-3 h-3 mr-1" /> Voltar para fotos
                  </Button>
                </div>

                <div className="flex items-center justify-center gap-2 pt-2 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                   <ShieldCheck className="w-4 h-4 text-emerald-500" />
                   Criptografia de Ponta a Ponta
                </div>
              </div>
            </div>
          )}
          
          {currentStep === "success" && (
            <div className="text-center max-w-md mx-auto animate-in zoom-in-95 duration-500">
              <div className="bg-emerald-500 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6 shadow-xl shadow-emerald-200 border-4 border-white">
                <CheckCircle className="h-10 w-10 text-white" />
              </div>
              <h2 className="text-3xl font-black mb-3 text-slate-900 uppercase tracking-tight">Análise Concluída!</h2>
              <p className="text-slate-600 mb-8 leading-relaxed">
                Seu pagamento foi reconhecido e o laudo técnico do seu veículo antigo já foi processado pela nossa perícia.
              </p>
              
              <div className="space-y-4">
                <Button 
                  className="w-full bg-slate-900 hover:bg-black text-white h-16 text-lg font-black shadow-2xl flex items-center justify-center gap-3 transition-transform hover:scale-[1.02]"
                  onClick={() => window.open(`https://siteplacapreta.onrender.com/cliente/${laudoId}`, '_blank')}
                >
                  <ExternalLink className="w-5 h-5 text-yellow-500" />
                  ABRIR RELATÓRIO TÉCNICO
                </Button>
                
                <Link to="/" className="block">
                  <Button variant="outline" className="w-full h-12 text-slate-400 font-bold border-slate-200 hover:bg-slate-50">
                    VOLTAR AO INÍCIO
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