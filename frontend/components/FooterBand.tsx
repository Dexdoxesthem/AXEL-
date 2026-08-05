export default function FooterBand() {
  return (
    <footer className="footer-band">
      <div className="icon-links">
        <a className="icon-link" href="/">
          <span className="icon-box">H</span> HOME
        </a>
        <a className="icon-link" href="/analytics">
          <span className="icon-box icon-box--peach">A</span> ANALYTICS
        </a>
        <a className="icon-link" href="/compare">
          <span className="icon-box icon-box--lime">C</span> COMPARE
        </a>
      </div>
      <div>
        AXEL&trade; Student Performance System &mdash; NAAC project. Built with a 1996 Dell in mind.
      </div>
    </footer>
  );
}
