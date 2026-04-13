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
  const [preferenceId, setPreferenceId] = useState<string | null>(null);

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

  // 1. Quando as fotos são enviadas, já buscamos a preferência de pagamento
  const handlePhotosSubmit = async (photoData: PhotoData) => {
    setPhotos(photoData);
    setCurrentStep("payment");
    
    try {
      const prefRes = await fetch("https://siteplacapreta.onrender.com/create_preference", {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });
      const data = await prefRes.json();
      setPreferenceId(data.id);
    } catch (err) {
      console.error("Erro ao criar preferência:", err);
    }
  };

  const handlePaymentAndGenerate = async () => {
    if (!window.MercadoPago || !preferenceId) {
      alert("Aguarde o carregamento do pagamento...");
      return;
    }

    setIsProcessing(true);

    try {
      // 2. Inicializar SDK
      const mp = new window.MercadoPago('APP_USR-9c54b89f-6fec-46ec-bde6-e975a8f1d962', {
        locale: 'pt-BR'
      });

      // 3. Abrir o Checkout (NÃO vamos usar autoOpen para evitar bloqueios)
      mp.checkout({
        preference: { id: preferenceId },
        autoOpen: true,
      });

      // 4. Enviar para o backend e SÓ mudar de tela se receber o ID do laudo
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
        // Só mudamos para a tela de sucesso se o backend confirmou a criação
        setTimeout(() => {
            setCurrentStep("success");
            setIsProcessing(false);
        }, 2000);
      }

    } catch (err) {
      console.error(err);
      setIsProcessing(false);
      alert("Erro ao processar. Verifique se o pop-up foi bloqueado.");
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
                  stepIndex[currentStep] >= i ? "bg-yellow-500 text-black shadow-[0_0_10px_rgba(234,179,8,0.5)]" : "bg-muted text-muted-foreground"
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
            <div className="max-w-md mx-auto p-8 bg-white rounded-2xl shadow-2xl border border-slate-100">
              <div className="text-center space-y-6">
                <CreditCard className="h-12 w-12 text-yellow-500 mx-auto" />
                <div className="space-y-2">
                  <h2 className="text-2xl font-black text-slate-900 uppercase">Checkout Seguro</h2>
                  <p className="text-slate-500 text-sm">Clique para pagar e gerar seu laudo técnico.</p>
                </div>
                
                <div className="bg-slate-50 p-6 rounded-xl border border-slate-100 text-left">
                  <span className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Resumo do Pedido</span>
                  <div className="flex justify-between items-center mt-2 border-t pt-2">
                    <span className="text-sm font-medium text-slate-700">Laudo Pericial IA</span>
                    <span className="text-xl font-black text-emerald-600">R$ 100,00</span>
                  </div>
                </div>

                <div className="flex flex-col gap-4">
                  <Button 
                    className="w-full h-16 text-lg bg-yellow-500 hover:bg-yellow-600 text-black font-black rounded-xl shadow-lg transition-all active:scale-95"
                    onClick={handlePaymentAndGenerate}
                    disabled={isProcessing || !preferenceId}
                  >
                    {isProcessing ? (
                      <div className="flex items-center gap-3">
                        <Loader2 className="animate-spin h-6 w-6" />
                        <span>PROCESSANDO...</span>
                      </div>
                    ) : (
                      "PAGAR AGORA"
                    )}
                  </Button>
                  
                  <Button variant="ghost" onClick={() => setCurrentStep("photos")} disabled={isProcessing} className="text-slate-400 text-xs">
                    <ArrowLeft className="w-3 h-3 mr-1" /> VOLTAR PARA FOTOS
                  </Button>
                </div>

                <div className="flex items-center justify-center gap-2 pt-2">
                   <ShieldCheck className="w-4 h-4 text-emerald-500" />
                   <span className="text-[10px] font-bold text-slate-400 uppercase">Ambiente Criptografado</span>
                </div>
              </div>
            </div>
          )}
          
          {currentStep === "success" && (
            <div className="text-center max-w-md mx-auto animate-in zoom-in-95 duration-500">
              <div className="bg-emerald-500 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6 shadow-xl">
                <CheckCircle className="h-12 w-12 text-white" />
              </div>
              <h2 className="text-3xl font-black mb-3 text-slate-900 uppercase">Laudo Gerado!</h2>
              <p className="text-slate-600 mb-8 leading-relaxed">
                A análise técnica foi concluída. Clique abaixo para visualizar o relatório completo.
              </p>
              
              <div className="space-y-4">
                <Button 
                  className="w-full bg-slate-900 hover:bg-black text-white h-16 text-lg font-black shadow-xl flex items-center justify-center gap-3"
                  onClick={() => window.open(`https://siteplacapreta.onrender.com/cliente/${laudoId}`, '_blank')}
                >
                  <ExternalLink className="w-5 h-5 text-yellow-500" />
                  ABRIR LAUDO TÉCNICO
                </Button>
                
                <Link to="/" className="block">
                  <Button variant="outline" className="w-full h-12 text-slate-400 font-bold border-slate-200">
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