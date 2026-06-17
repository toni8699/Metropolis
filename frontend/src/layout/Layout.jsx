import Footer from "@/layout/Footer";
import Header from "@/layout/Header";

export default function Layout({ children, onSearch, onHome }) {
  return (
    <div className="flex min-h-screen flex-col text-vroom-text">
      <Header onSearch={onSearch} onHome={onHome} />
      <main className="container-x flex min-h-0 flex-1 flex-col py-[var(--app-content-gap)]">
        {children}
      </main>
      <Footer />
    </div>
  );
}
