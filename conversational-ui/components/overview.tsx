import { motion } from 'framer-motion';
import Link from 'next/link';

import { MessageIcon, VercelIcon } from './icons';

export const Overview = () => {
  return (
    <motion.div
      key="overview"
      className="max-w-3xl mx-auto md:mt-20"
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.98 }}
      transition={{ delay: 0.5 }}
    >
      <div className="rounded-xl p-6 flex flex-col gap-8 leading-relaxed text-center max-w-xl">
      <h1 className="mb-2 text-lg font-semibold">
          Welcome to umans.ai platform!
        </h1>
        <p className="mb-2 leading-normal text-muted-foreground">
        umans.ai is a multi-AI agent platform designed to help software development teams master complexity and deliver value continuously.
        </p>
        <p className="leading-normal text-muted-foreground">
          You can start a conversation here or try the following examples 👇
        </p>
      </div>
    </motion.div>
  );
};
