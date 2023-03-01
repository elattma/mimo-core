import Nav from "./nav";
import Options from "./options";

const AppHeader = () => {
  return (
    <header className="sticky top-0 flex w-full items-center justify-between border-b border-b-neutral-border bg-neutral-base py-theme-1/2 px-theme">
      <Nav />
      <Options />
    </header>
  );
};

export default AppHeader;
