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

  // 🚀 ENVIO PARA BACKEND
  const enviarParaBackend = async () => {
    if (!formData) return;

    const form = new FormData();

    // 👤 cliente
    form.append("nome", formData.nome);
    form.append("email", formData.email);
    form.append("telefone", formData.telefone);
    form.append("cidade", formData.cidade);
    form.append("estado", formData.estado);

    // 🚗 veículo
    form.append("marca", formData.marca);
    form.append("modelo", formData.modelo);
    form.append("ano", formData.ano);
    form.append("placa", formData.placa);
    form.append("cor", formData.cor);
    form.append("motorizacao", formData.motorizacao);
    form.append("observacao", formData.observacao || "");

    // 📸 DEBUG + ENVIO DAS FOTOS
    console.log("🔥 FOTOS QUE ESTÃO SENDO ENVIADAS:");
    Object.entries(photos).forEach(([key, file]) => {
      console.log(key, file);

      if (file instanceof File) {
        form.append(`foto_${key}`, file);
      }
    });

    const res = await fetch("//siteplacapreta.onrender.com/avaliacao", {
      method: "POST",
      body: form,
    });

    if (!res.ok) {
      throw new Error("Erro ao enviar avaliação");
    }

    return await res.json();
  };

  const handlePayment = async () => {
    setIsProcessing(true);

    try {
      const resposta = await enviarParaBackend();
      console.log("🔥 RESPOSTA BACKEND:", resposta);

      setTimeout(() => {
        setIsProcessing(false);
        setCurrentStep("success");
      }, 1200);

    } catch (err) {
      console.error(err);
      setIsProcessing(false);
      alert("Erro ao enviar avaliação");
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

          {/* ETAPAS */}
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
                Avaliação enviada com sucesso!
              </h2>
              <p className="text-gray-500 mt-2">
                Você receberá o resultado no email.
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