import { Facebook, Globe, Instagram, Twitter } from "lucide-react";

function FooterColumn({ title, links }) {
  return (
    <div>
      <h3 className="mb-3 text-lg font-extrabold text-vroom-heading">{title}</h3>
      <div className="flex flex-col gap-2">
        {links.map((link) => (
          <a
            key={link}
            href="#"
            className="text-sm font-medium text-vroom-muted hover:underline"
          >
            {link}
          </a>
        ))}
      </div>
    </div>
  );
}

export default function Footer() {
  return (
    <footer className="container-x w-full border-t-4 border-black bg-vroom-surface py-10">
      <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
          <FooterColumn
            title="Support"
            links={[
              "Help Center",
              "Cancellation options",
              "Report a concern",
              "Accessibility support",
            ]}
          />
          <FooterColumn
            title="Company"
            links={["About us", "Careers", "Press", "Investors"]}
          />
          <FooterColumn
            title="Hosting"
            links={[
              "Host your car",
              "Hosting resources",
              "Community forum",
              "Responsible hosting",
            ]}
          />
        </div>

        <div className="mt-8 flex flex-col gap-4 border-t-2 border-black pt-6 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-wrap items-center gap-2 text-sm font-medium text-vroom-muted">
            <span>© 2024 VROOM, Inc.</span>
            <span>·</span>
            <a href="#" className="hover:underline">
              Terms
            </a>
            <span>·</span>
            <a href="#" className="hover:underline">
              Privacy
            </a>
            <span>·</span>
            <a href="#" className="hover:underline">
              Sitemap
            </a>
          </div>

          <div className="flex items-center gap-4 text-vroom-muted">
            <button className="flex items-center gap-1 text-sm font-semibold hover:underline">
              <Globe className="h-4 w-4" />
              English (CA)
            </button>
            <button className="text-sm font-semibold hover:underline">CAD</button>
            <a href="#" aria-label="Facebook" className="rounded-full border-2 border-black bg-vroom-coral p-1 hover:text-black">
              <Facebook className="h-4 w-4" />
            </a>
            <a href="#" aria-label="Twitter" className="rounded-full border-2 border-black bg-vroom-gold p-1 hover:text-black">
              <Twitter className="h-4 w-4" />
            </a>
            <a href="#" aria-label="Instagram" className="rounded-full border-2 border-black bg-vroom-surface p-1 hover:text-black">
              <Instagram className="h-4 w-4" />
            </a>
          </div>
        </div>
    </footer>
  );
}
