const UploadedItems = () => {
  return (
    <div className="space-y-theme-1/2">
      <p className="text-sm font-medium text-gray-text-contrast">
        Uploaded Items
      </p>
      <div className="rounded-theme border border-dashed border-neutral-border p-theme">
        <p className="text-center text-sm text-neutral-text">
          Click here to upload an item or drag and drop anywhere.
        </p>
      </div>
    </div>
  );
};

export default UploadedItems;
