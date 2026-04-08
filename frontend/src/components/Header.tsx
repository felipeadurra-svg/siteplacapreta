import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Car } from "lucide-react";

const Header = () => {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-xl">
      <div className="container flex h-16 items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <Car className="h-6 w-6 text-primary" />
          <span className="font-heading text-lg font-bold text-gradient-gold">Placa Preta</span>
        </Link>
        <nav className="hidden md:flex items-center gap-8">
          <Link to="/" className="text-sm text-muted-foreground hover:text-primary transition-colors">Início</Link>
          <Link to="/avaliacao" className="text-sm text-muted-foreground hover:text-primary transition-colors">Avaliação</Link>
          </nav>
        <Link to="/avaliacao">
          <Button variant="gold" size="sm">Iniciar Avaliação</Button>
        </Link>
      </div>
    </header>
  );
};

export default Header;
