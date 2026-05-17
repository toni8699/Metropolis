import Footer from "./Footer";
import Header from "./Header";

export default function Layout({ children, onSearch, onHome }) {
  return (
    <div className="min-h-screen flex flex-col bg-white text-gray-900">
      <Header onSearch={onSearch} onHome={onHome} />
      <main className="w-full flex-grow pt-40 md:pt-36">{children}</main>
      <Footer />
    </div>
  );
}
