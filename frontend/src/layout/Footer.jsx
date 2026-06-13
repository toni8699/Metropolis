import { Facebook, Globe, Instagram, Twitter } from "lucide-react";

function FooterColumn({ title, links }) {
  return (
    <div>
      <h3 className="mb-3 text-lg font-extrabold text-[#183B1E]">{title}</h3>
      <div className="flex flex-col gap-2">
        {links.map((link) => (
          <a
            key={link}
            href="#"
            className="text-sm font-medium text-[#35593b] hover:underline"
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
    <footer className="w-full border-t-4 border-black bg-[#FCFCE5] px-4 py-10 sm:px-6 md:px-10 lg:px-12 xl:px-20">
      <div>
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
          <div className="flex flex-wrap items-center gap-2 text-sm font-medium text-[#35593b]">
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

          <div className="flex items-center gap-4 text-[#35593b]">
            <button className="flex items-center gap-1 text-sm font-semibold hover:underline">
              <Globe className="h-4 w-4" />
              English (CA)
            </button>
            <button className="text-sm font-semibold hover:underline">CAD</button>
            <a href="#" aria-label="Facebook" className="rounded-full border-2 border-black bg-[#F8AFA1] p-1 hover:text-black">
              <Facebook className="h-4 w-4" />
            </a>
            <a href="#" aria-label="Twitter" className="rounded-full border-2 border-black bg-[#FFD166] p-1 hover:text-black">
              <Twitter className="h-4 w-4" />
            </a>
            <a href="#" aria-label="Instagram" className="rounded-full border-2 border-black bg-[#FCFCE5] p-1 hover:text-black">
              <Instagram className="h-4 w-4" />
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
