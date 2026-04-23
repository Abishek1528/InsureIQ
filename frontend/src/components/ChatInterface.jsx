import React, { useState, useEffect, useRef } from 'react';
import { sendChatMessage } from '../services/api';

const ChatInterface = ({ sessionId }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([
        { text: "Hi! I'm your InsureIQ assistant. Ask me anything about your policy recommendations!", isBot: true }
    ]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim() || !sessionId) return;

        const userMessage = input.trim();
        setInput("");
        setMessages(prev => [...prev, { text: userMessage, isBot: false }]);
        setLoading(true);

        try {
            const response = await sendChatMessage(sessionId, userMessage);
            setMessages(prev => [...prev, { 
                text: response.answer, 
                isBot: true,
                sources: response.sources 
            }]);
        } catch (error) {
            setMessages(prev => [...prev, { 
                text: "Sorry, I encountered an error. Please try again.", 
                isBot: true,
                isError: true 
            }]);
        } finally {
            setLoading(false);
        }
    };

    if (!sessionId) return null;

    return (
        <div className={`chat-container ${isOpen ? 'open' : ''}`}>
            {/* Chat Bubble Toggle */}
            <button 
                className="chat-toggle" 
                onClick={() => setIsOpen(!isOpen)}
                title="Chat with AI"
            >
                {isOpen ? '✕' : '💬'}
            </button>

            {/* Chat Window */}
            <div className="chat-window">
                <div className="chat-header">
                    <h3>AI Policy Assistant</h3>
                    <p>Powered by InsureIQ RAG</p>
                </div>

                <div className="chat-messages">
                    {messages.map((msg, index) => (
                        <div key={index} className={`message ${msg.isBot ? 'bot' : 'user'} ${msg.isError ? 'error' : ''}`}>
                            <div className="message-content">
                                {msg.text}
                                {msg.sources && msg.sources.length > 0 && (
                                    <div className="message-sources">
                                        <span>Sources:</span>
                                        {msg.sources.map((src, i) => (
                                            <span key={i} className="source-tag">
                                                {src.source} (p.{src.page})
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                    {loading && (
                        <div className="message bot loading">
                            <div className="typing-indicator">
                                <span></span><span></span><span></span>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                <form className="chat-input-area" onSubmit={handleSend}>
                    <input 
                        type="text" 
                        placeholder="Ask a question..." 
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        disabled={loading}
                    />
                    <button type="submit" disabled={loading || !input.trim()}>
                        ➤
                    </button>
                </form>
            </div>
        </div>
    );
};

export default ChatInterface;
