import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ArrowRight, Shield, Award } from "lucide-react";
import heroCar from "@/assets/hero-car.jpg";

const HeroSection = () => {
  return (
    <section className="relative min-h-[90vh] flex items-center justify-center overflow-hidden">
      {/* Background Image */}
      <div className="absolute inset-0">
        <img
          src={heroCar}
          alt="Carro clássico vintage"
          width={1920}
          height={1080}
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-background via-background/80 to-background/40" />
        <div className="absolute inset-0 bg-gradient-to-r from-background/60 to-transparent" />
      </div>

      <div className="container relative z-10 flex flex-col items-center text-center px-4 py-20">
        <div className="flex items-center gap-2 mb-6 animate-fade-in">
          <Shield className="h-4 w-4 text-primary" />
          <span className="text-xs uppercase tracking-[0.3em] text-primary font-medium">
            Certificação Oficial
          </span>
          <Shield className="h-4 w-4 text-primary" />
        </div>

        <h1 className="font-heading text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold leading-tight mb-6 animate-fade-up max-w-4xl">
          Avaliação de Veículos Antigos para{" "}
          <span className="text-gradient-gold">Placa Preta</span>
        </h1>

        <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mb-10 animate-fade-up" style={{ animationDelay: '0.2s' }}>
          Envie as fotos do seu veículo e receba um relatório técnico profissional
          com análise de originalidade e conservação, no padrão FBVA.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 animate-fade-up" style={{ animationDelay: '0.4s' }}>
          <Link to="/avaliacao">
            <Button variant="gold" size="lg" className="text-base px-8 py-6">
              Iniciar Avaliação
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </Link>
          <a href="#como-funciona">
            <Button variant="goldOutline" size="lg" className="text-base px-8 py-6">
              Como Funciona
            </Button>
          </a>
        </div>

        <div className="flex items-center gap-8 mt-16 animate-fade-up" style={{ animationDelay: '0.6s' }}>
          <div className="flex items-center gap-2">
            <Award className="h-5 w-5 text-primary" />
            <span className="text-sm text-muted-foreground">Padrão FBVA</span>
          </div>
          <div className="h-4 w-px bg-border" />
          <span className="text-sm text-muted-foreground">Análise com IA</span>
          <div className="h-4 w-px bg-border" />
          <span className="text-sm text-muted-foreground">Relatório PDF</span>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
