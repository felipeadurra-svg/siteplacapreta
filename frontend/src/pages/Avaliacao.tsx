import { useState } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import VehicleForm, { type AvaliacaoFormData } from "@/components/VehicleForm";
import PhotoUpload, { type PhotoData } from "@/components/PhotoUpload";
import PaymentPage from "@/components/PaymentPage";
import { CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

type Step = "form" | "photos" | "payment" | "success";

const Avaliacao = () => {
  const [currentStep, setCurrentStep] = useState<Step>("form");
  const [formData, setFormData] = useState<AvaliacaoFormData | null>(null);
  const [photos, setPhotos] = useState<PhotoData>({});
  const [isProcessing, setIsProcessing] = useState(false);

  const stepIndex = { form: 0, photos: 1, payment: 2, success: 3 };
  const steps = ["Dados", "Fotos", "Pagamento", "Concluído"];

  const handleFormSubmit = (data: AvaliacaoFormData) => {
    setFormData(data);
    setCurrentStep("photos");
  };

  const handlePhotosSubmit = (photoData: PhotoData) => {
    setPhotos(photoData);
    setCurrentStep("payment");
  };

  // 🚀 LÓGICA DE ENVIO E REDIRECIONAMENTO
  const handlePayment = async () => {
    if (!formData) return;
    setIsProcessing(true);

    const form = new FormData();

    // 👤 Dados do Cliente
    form.append("nome", formData.nome);
    form.append("email", formData.email);
    form.append("telefone", formData.telefone);
    form.append("cidade", formData.cidade);
    form.append("estado", formData.estado);

    // 🚗 Dados do Veículo
    form.append("marca", formData.marca);
    form.append("modelo", formData.modelo);
    form.append("ano", formData.ano);
    form.append("placa", formData.placa);
    form.append("cor", formData.cor);
    form.append("motorizacao", formData.motorizacao);
    form.append("observacao", formData.observacao || "");

    // 📸 Anexando Fotos
    console.log("🔥 Iniciando envio das fotos para o backend...");
    Object.entries(photos).forEach(([key, file]) => {
      if (file instanceof File) {
        // O backend espera foto_frente, foto_traseira, etc.
        form.append(`foto_${key}`, file);
      }
    });

    try {
      const res = await fetch("//siteplacapreta.onrender.com/avaliacao", {
        method: "POST",
        body: form,
        redirect: "follow", // IMPORTANTE: Segue o RedirectResponse do FastAPI
      });

      if (!res.ok) {
        throw new Error("Erro na resposta do servidor");
      }

      // 🏁 O Backend redireciona para /cliente/{id}
      // O res.url conterá o endereço final do laudo gerado
      const urlFinalDoLaudo = res.url;
      console.log("✅ Laudo gerado com sucesso em:", urlFinalDoLaudo);

      setTimeout(() => {
        setIsProcessing(false);
        // Em vez de mudar para a etapa "success", enviamos direto para o laudo
        window.location.href = urlFinalDoLaudo;
      }, 500);

    } catch (err) {
      console.error("❌ Erro no envio:", err);
      setIsProcessing(false);
      alert("Houve um erro ao processar sua avaliação. Por favor, tente novamente.");
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="pt-16">
        <div className="container py-12 px-4">

          {/* STEPPER */}
          <div className="flex items-center justify-center gap-2 mb-12">
            {steps.map((label, i) => (
              <div key={label} className="flex items-center gap-2">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                  stepIndex[currentStep] >= i
                    ? "bg-yellow-500 text-black"
                    : "bg-gray-300"
                }`}>
                  {i + 1}
                </div>
                <span className="text-xs">{label}</span>
              </div>
            ))}
          </div>

          {/* CONTEÚDO DAS ETAPAS */}
          {currentStep === "form" && (
            <VehicleForm onSubmit={handleFormSubmit} />
          )}

          {currentStep === "photos" && (
            <PhotoUpload
              onSubmit={handlePhotosSubmit}
              onBack={() => setCurrentStep("form")}
            />
          )}

          {currentStep === "payment" && (
            <PaymentPage
              onPaymentConfirm={handlePayment}
              onBack={() => setCurrentStep("photos")}
              isProcessing={isProcessing}
            />
          )}

          {currentStep === "success" && (
            <div className="text-center">
              <CheckCircle className="mx-auto h-16 w-16 text-green-500" />
              <h2 className="text-2xl font-bold mt-4">
                Avaliação processada!
              </h2>
              <p className="text-gray-500 mt-2">
                Seu laudo técnico foi gerado e está pronto para visualização.
              </p>

              <Link to="/">
                <Button className="mt-6">Voltar ao início</Button>
              </Link>
            </div>
          )}

        </div>
      </main>

      <Footer />
    </div>
  );
};

export default Avaliacao;