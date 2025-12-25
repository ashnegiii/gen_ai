'use client';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Loader2, Send, Sparkles, User } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';

interface Message {
	id: string;
	role: 'user' | 'assistant';
	content: string;
	timestamp: string;
}

export default function Chat() {
	const [messages, setMessages] = useState<Message[]>([
		{
			id: 'welcome',
			role: 'assistant',
			content: '',
			timestamp: new Date().toLocaleTimeString('en-US', {
				hour: '2-digit',
				minute: '2-digit',
			}),
		},
	]);

	const [input, setInput] = useState('');
	const [isLoading, setIsLoading] = useState(false);
	const messagesEndRef = useRef<HTMLDivElement>(null);

	const scrollToBottom = () => {
		messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
	};

	useEffect(() => {
		scrollToBottom();
	}, [messages]);

	useEffect(() => {
		const welcomeText =
			'Hey! I am your AI assistant. I can help you answer questions based on your uploaded documents. Feel free to ask me anything.';

		let index = 0;

		const interval = setInterval(() => {
			setMessages((prev) => {
				const updated = [...prev];
				updated[0] = {
					...updated[0],
					content: welcomeText.slice(0, index + 1),
				};
				return updated;
			});

			index++;

			if (index >= welcomeText.length) {
				clearInterval(interval);
			}
		}, 5); // typing speed type shi

		return () => clearInterval(interval);
	}, []);

	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault();

		if (!input.trim() || isLoading) return;

		const userMessage: Message = {
			id: Date.now().toString(),
			role: 'user',
			content: input.trim(),
			timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
		};

		setMessages((prev) => [...prev, userMessage]);
		setInput('');
		setIsLoading(true);

		// Add a placeholder assistant message that will be updated with streaming content
		const assistantMessageId = (Date.now() + 1).toString();
		const assistantMessage: Message = {
			id: assistantMessageId,
			role: 'assistant',
			content: '',
			timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
		};
		setMessages((prev) => [...prev, assistantMessage]);

		try {
			const backendUrl = process.env.NEXT_PUBLIC_BACKEND_CHAT_URL || 'http://localhost:5000/api/chat';

			const response = await fetch(backendUrl, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ query: userMessage.content }),
			});

			if (!response.ok) {
				throw new Error('Failed to get response');
			}

			// Handle streaming response
			const reader = response.body?.getReader();
			const decoder = new TextDecoder();

			if (!reader) {
				throw new Error('No response body');
			}

			let accumulatedContent = '';

			while (true) {
				const { done, value } = await reader.read();

				if (done) break;

				const chunk = decoder.decode(value, { stream: true });
				accumulatedContent += chunk;

				// Update the assistant message with accumulated content
				setMessages((prev) =>
					prev.map((msg) => (msg.id === assistantMessageId ? { ...msg, content: accumulatedContent } : msg))
				);
			}
		} catch (error) {
			console.error('Chat error:', error);

			// Update the assistant message with error content
			setMessages((prev) =>
				prev.map((msg) =>
					msg.id === assistantMessageId
						? { ...msg, content: 'Sorry, I encountered an error. Please try again.' }
						: msg
				)
			);

			toast.error('Error', { description: 'Failed to get response. Please try again.' });
		} finally {
			setIsLoading(false);
		}
	};

	const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			handleSubmit(e);
		}
	};

	return (
		<div className='h-screen bg-background flex flex-col'>
			<header className='border-b border-border shrink-0'>
				<div className='container mx-auto px-4 py-4'>
					<nav className='flex items-center justify-between'>
						<div className='flex items-center gap-8'>
							<h1 className='text-xl font-semibold'>Chadoc</h1>
							<div className='flex gap-6 text-sm'>
								<Link
									href='/'
									className='text-muted-foreground hover:text-foreground transition-colors'
								>
									Documents
								</Link>
								<Link
									href='/chat'
									className='text-foreground font-medium'
								>
									Chat
								</Link>
							</div>
						</div>
					</nav>
				</div>
			</header>
			<main className='flex-1 overflow-hidden flex flex-col'>
				<div className='container mx-auto px-4 flex-1 flex flex-col max-w-4xl overflow-hidden'>
					<div className='flex-1 overflow-y-auto py-8 space-y-6'>
						{messages.map((message, i) => (
							<div
								key={i}
								className={`flex gap-4 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
							>
								{message.role === 'assistant' && (
									<div className='shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center'>
										<Sparkles className='h-4 w-4' />
									</div>
								)}
								<Card className='px-4 py-3 gap-2 max-w-[80%]'>
									{message.role === 'assistant' && isLoading && message.content === '' ? (
										<Loader2 className='h-4 w-4 animate-spin text-muted-foreground' />
									) : (
										<p className='text-sm leading-relaxed whitespace-pre-wrap'>{message.content}</p>
									)}
									<p className='text-xs text-muted-foreground'>{message.timestamp}</p>
								</Card>

								{message.role === 'user' && (
									<div className='shrink-0 w-8 h-8 rounded-full bg-secondary text-secondary-foreground flex items-center justify-center'>
										<User className='h-4 w-4' />
									</div>
								)}
							</div>
						))}
						<div ref={messagesEndRef} />
					</div>

					<div className='border-t border-border py-4 shrink-0 bg-background'>
						<form
							onSubmit={handleSubmit}
							className='flex gap-2'
						>
							<Textarea
								value={input}
								onChange={(e) => setInput(e.target.value)}
								onKeyDown={handleKeyDown}
								placeholder='Ask a question about your documents...'
								className='min-h-15 max-h-50 resize-none'
							/>
							<Button
								type='submit'
								size='icon'
								disabled={isLoading || !input.trim()}
								className='h-15 w-15 shrink-0'
							>
								{isLoading ? (
									<Loader2 className='h-5 w-5 animate-spin' />
								) : (
									<Send className='h-5 w-5' />
								)}
							</Button>
						</form>
						<p className='text-xs text-muted-foreground mt-2'>
							Press Enter to send, Shift+Enter for new line
						</p>
					</div>
				</div>
			</main>
		</div>
	);
}
