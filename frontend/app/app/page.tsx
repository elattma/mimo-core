import Link from "next/link";

const Page = () => {
  return (
    <>
      App home page. Navigate to{" "}
      <Link className="text-blue-500 underline" href="/app/chat">
        /chat
      </Link>{" "}
      for the time being.
    </>
  );
};

export default Page;
