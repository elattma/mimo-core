import IntegrationsManager from "./integrations-manager";
import Items from "./items";

const IntegratedItems = () => {
  return (
    <div className="space-y-theme-1/2">
      <p className="text-sm font-medium text-gray-text-contrast">
        Integrated Items
      </p>
      <IntegrationsManager />
      {/* @ts-expect-error Server Component */}
      <Items />
    </div>
  );
};

export default IntegratedItems;
