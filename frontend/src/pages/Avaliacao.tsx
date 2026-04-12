import { useState, useEffect } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import VehicleForm, { type AvaliacaoFormData } from "@/components/VehicleForm";
import PhotoUpload, { type PhotoData } from "@/components/PhotoUpload";
import PaymentPage from "@/components/PaymentPage";
import { CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

type Step = "form" | "photos" | "payment" | "success";

// 1. Melhoria na declaração global para evitar erros de compilação
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
  // 2. Tipagem explícita para o indexador evitar erro de TS7053
  const stepIndex: Record<Step, number> = { form: 0, photos: 1, payment: 2, success: 3 };

  useEffect(() => {
    // 3. Verificação para não carregar o script múltiplas vezes
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
    // 4. Verificação de segurança: O SDK carregou?
    if (!window.MercadoPago) {
      alert("O sistema de pagamento ainda está carregando. Por favor, aguarde um instante.");
      return;
    }

    setIsProcessing(true);

    try {
      const prefRes = await fetch("https://siteplacapreta.onrender.com/create_preference", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items: [{ title: "Laudo Tecnico", unit_price: 99.90 }] })
      });
      
      const { id: preferenceId } = await prefRes.json();

      // 5. Inicialização correta
      const mp = new window.MercadoPago('APP_USR-9c54b89f-6fec-46ec-bde6-e975a8f1d962', {
        locale: 'pt-BR'
      });

      // Abre o checkout (procedimento padrão para integração Pro/Modal)
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
      }, 2000);

    } catch (err) {
      console.error(err);
      setIsProcessing(false);
      alert("Erro ao processar pagamento ou gerar laudo.");
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-16">
        <div className="container py-12 px-4">
          <div className="flex items-center justify-center gap-2 mb-12">
            {steps.map((label, i) => (
              <div key={label} className="flex items-center gap-2">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                  stepIndex[currentStep] >= i ? "bg-yellow-500 text-black" : "bg-gray-300"
                }`}>
                  {i + 1}
                </div>
                <span className="text-xs">{label}</span>
              </div>
            ))}
          </div>

          {currentStep === "form" && <VehicleForm onSubmit={handleFormSubmit} />}
          {currentStep === "photos" && <PhotoUpload onSubmit={handlePhotosSubmit} onBack={() => setCurrentStep("form")} />}
          {currentStep === "payment" && <PaymentPage onPaymentConfirm={handlePayment} onBack={() => setCurrentStep("photos")} isProcessing={isProcessing} />}
          
          {currentStep === "success" && (
            <div className="text-center animate-in fade-in duration-700">
              <CheckCircle className="mx-auto h-16 w-16 text-green-500" />
              <h2 className="text-2xl font-bold mt-4">Avaliação enviada com sucesso!</h2>
              <p className="text-gray-500 mt-2">O pagamento foi processado e seu laudo técnico já está disponível.</p>
              <div className="flex flex-col gap-3 items-center mt-6">
                <Button 
                  className="bg-green-700 hover:bg-green-800 text-white px-8 h-12 text-lg"
                  onClick={() => window.open(`https://siteplacapreta.onrender.com/cliente/${laudoId}`, '_blank')}
                >
                  Visualizar Laudo Técnico
                </Button>
                <Link to="/"><Button variant="ghost" className="mt-2">Voltar ao início</Button></Link>
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