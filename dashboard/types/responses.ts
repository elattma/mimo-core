export type GetEndpoints = {
  "/locksmith": GetLocksmithResponse;
};

export type GetLocksmithResponse = {
  apiKey: {
    value: string;
  };
};

export type PostEndpoints = {
  "/locksmith": PostLocksmithResponse;
};

export type PostLocksmithResponse = {
  apiKey: {
    value: string;
  };
};
