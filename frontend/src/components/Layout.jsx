import Footer from "./Footer";
import Header from "./Header";

export default function Layout({ children, onSearch }) {
  return (
    <div className="min-h-screen flex flex-col bg-white text-gray-900">
      <Header onSearch={onSearch} />
      <main className="w-full flex-grow pt-24 md:pt-28">{children}</main>
      <Footer />
    </div>
  );
}
