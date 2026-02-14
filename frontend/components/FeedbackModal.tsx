"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Send, AlertCircle, MessageSquare, Bug, Lightbulb, Loader2 } from "lucide-react";
import { useI18n } from "@/lib/i18n";
import { submitReport } from "@/lib/api";

interface FeedbackModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export function FeedbackModal({ isOpen, onClose }: FeedbackModalProps) {
    const { t } = useI18n();
    const [type, setType] = useState<"bug" | "feature" | "other">("bug");
    const [message, setMessage] = useState("");
    const [email, setEmail] = useState("");
    const [status, setStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!message.trim()) return;

        setStatus("submitting");
        try {
            await submitReport({
                type,
                message,
                email: email || undefined,
            });
            setStatus("success");
            setTimeout(() => {
                onClose();
                setStatus("idle");
                setMessage("");
                setEmail("");
            }, 2000);
        } catch (error) {
            console.error(error);
            setStatus("error");
        }
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100]"
                        onClick={onClose}
                    />
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        className="fixed inset-0 m-auto w-full max-w-md h-fit glass-premium rounded-2xl shadow-2xl z-[101] overflow-hidden"
                    >
                        <div className="p-6">
                            <div className="flex items-center justify-between mb-6">
                                <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                                    <MessageSquare className="w-5 h-5 text-[#00E0C6]" />
                                    Sorun Bildir
                                </h2>
                                <button
                                    onClick={onClose}
                                    className="p-2 hover:bg-white/5 rounded-full text-gray-400 hover:text-white transition-colors"
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>

                            {status === "success" ? (
                                <div className="text-center py-8">
                                    <motion.div
                                        initial={{ scale: 0 }}
                                        animate={{ scale: 1 }}
                                        className="w-16 h-16 bg-green-500/20 text-green-500 rounded-full flex items-center justify-center mx-auto mb-4"
                                    >
                                        <Send className="w-8 h-8" />
                                    </motion.div>
                                    <h3 className="text-lg font-medium text-white mb-2">Gönderildi!</h3>
                                    <p className="text-gray-400">Geri bildiriminiz için teşekkürler.</p>
                                </div>
                            ) : (
                                <form onSubmit={handleSubmit} className="space-y-4">
                                    <div className="grid grid-cols-3 gap-2">
                                        <button
                                            type="button"
                                            onClick={() => setType("bug")}
                                            className={`p-3 rounded-xl border flex flex-col items-center gap-2 transition-all ${type === "bug"
                                                ? "bg-red-500/10 border-red-500/50 text-red-500"
                                                : "bg-white/5 border-transparent text-gray-400 hover:bg-white/10"
                                                }`}
                                        >
                                            <Bug className="w-5 h-5" />
                                            <span className="text-xs font-medium">Hata</span>
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => setType("feature")}
                                            className={`p-3 rounded-xl border flex flex-col items-center gap-2 transition-all ${type === "feature"
                                                ? "bg-blue-500/10 border-blue-500/50 text-blue-500"
                                                : "bg-white/5 border-transparent text-gray-400 hover:bg-white/10"
                                                }`}
                                        >
                                            <Lightbulb className="w-5 h-5" />
                                            <span className="text-xs font-medium">Öneri</span>
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => setType("other")}
                                            className={`p-3 rounded-xl border flex flex-col items-center gap-2 transition-all ${type === "other"
                                                ? "bg-[#00E0C6]/10 border-[#00E0C6]/50 text-[#00E0C6]"
                                                : "bg-white/5 border-transparent text-gray-400 hover:bg-white/10"
                                                }`}
                                        >
                                            <MessageSquare className="w-5 h-5" />
                                            <span className="text-xs font-medium">Diğer</span>
                                        </button>
                                    </div>

                                    <div className="space-y-1.5">
                                        <label className="text-sm font-medium text-gray-400">Mesajınız</label>
                                        <textarea
                                            value={message}
                                            onChange={(e) => setMessage(e.target.value)}
                                            placeholder="Lütfen detaylı bilgi verin..."
                                            className="w-full h-32 bg-black/20 border border-white/10 rounded-xl p-3 text-white placeholder-gray-600 focus:outline-none focus:border-[#00E0C6]/50 resize-none"
                                            required
                                        />
                                    </div>

                                    <div className="space-y-1.5">
                                        <label className="text-sm font-medium text-gray-400">E-posta (Opsiyonel)</label>
                                        <input
                                            type="email"
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            placeholder="Size geri dönüş yapabilmemiz için..."
                                            className="w-full bg-black/20 border border-white/10 rounded-xl p-3 text-white placeholder-gray-600 focus:outline-none focus:border-[#00E0C6]/50"
                                        />
                                    </div>

                                    <button
                                        type="submit"
                                        disabled={status === "submitting" || !message.trim()}
                                        className="w-full py-3 bg-gradient-to-r from-[#00E0C6] to-[#3B82F6] text-[#0B1220] font-semibold rounded-xl hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                    >
                                        {status === "submitting" ? (
                                            <>
                                                <Loader2 className="w-5 h-5 animate-spin" />
                                                Gönderiliyor...
                                            </>
                                        ) : (
                                            "Gönder"
                                        )}
                                    </button>
                                </form>
                            )}
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
