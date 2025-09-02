import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import { Button } from './components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Textarea } from './components/ui/textarea';
import { Badge } from './components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { toast } from 'sonner';
import { Toaster } from './components/ui/sonner';
import { Mic, MicOff, Play, RefreshCw, MessageCircle, Target, Users } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [currentMode, setCurrentMode] = useState('home');
  const [scenarios, setScenarios] = useState([]);
  const [practiceScenarios, setPracticeScenarios] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recordedText, setRecordedText] = useState('');
  const [aiResponse, setAiResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentPracticeIndex, setCurrentPracticeIndex] = useState(0);
  const [practiceResponse, setPracticeResponse] = useState('');
  const [practiceFeedback, setPracticeFeedback] = useState(null);
  const [selectedLanguage, setSelectedLanguage] = useState('English');
  const [practiceRecordedText, setPracticeRecordedText] = useState('');
  const [practiceIsRecording, setPracticeIsRecording] = useState(false);

  const recognitionRef = useRef(null);
  const practiceRecognitionRef = useRef(null);

  const languages = [
    'English', 'Hindi', 'Hinglish', 'Marathi', 'Kannada', 'Tamil', 'Telugu', 'Bangla'
  ];

  useEffect(() => {
    fetchScenarios();
    fetchCategories();
  }, []);

  const fetchScenarios = async () => {
    try {
      const response = await axios.get(`${API}/scenarios`);
      setScenarios(response.data);
    } catch (error) {
      toast.error('Failed to load scenarios');
      console.error(error);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${API}/scenarios/categories`);
      setCategories(response.data.categories);
    } catch (error) {
      console.error('Failed to load categories', error);
    }
  };

  const fetchPracticeScenarios = async () => {
    try {
      const response = await axios.get(`${API}/scenarios/practice`);
      setPracticeScenarios(response.data);
      setCurrentPracticeIndex(0);
    } catch (error) {
      toast.error('Failed to load practice scenarios');
      console.error(error);
    }
  };

  const startRecording = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      toast.error('Speech recognition not supported in this browser');
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognitionRef.current = new SpeechRecognition();
    
    recognitionRef.current.continuous = true;
    recognitionRef.current.interimResults = true;
    recognitionRef.current.lang = getLanguageCode(selectedLanguage);

    recognitionRef.current.onstart = () => {
      setIsRecording(true);
      toast.success('Recording started...');
    };

    recognitionRef.current.onresult = (event) => {
      const current = event.resultIndex;
      const transcript = event.results[current][0].transcript;
      setRecordedText(transcript);
    };

    recognitionRef.current.onerror = (event) => {
      console.error('Speech recognition error', event.error);
      toast.error('Recording error: ' + event.error);
      setIsRecording(false);
    };

    recognitionRef.current.onend = () => {
      setIsRecording(false);
    };

    recognitionRef.current.start();
  };

  const stopRecording = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setIsRecording(false);
  };

  const startPracticeRecording = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      toast.error('Speech recognition not supported in this browser');
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    practiceRecognitionRef.current = new SpeechRecognition();
    
    practiceRecognitionRef.current.continuous = true;
    practiceRecognitionRef.current.interimResults = true;
    practiceRecognitionRef.current.lang = 'en-US'; // Default to English for practice

    practiceRecognitionRef.current.onstart = () => {
      setPracticeIsRecording(true);
      toast.success('Recording started...');
    };

    practiceRecognitionRef.current.onresult = (event) => {
      const current = event.resultIndex;
      const transcript = event.results[current][0].transcript;
      setPracticeRecordedText(transcript);
      setPracticeResponse(transcript); // Also update the main response field
    };

    practiceRecognitionRef.current.onerror = (event) => {
      console.error('Practice speech recognition error', event.error);
      toast.error('Recording error: ' + event.error);
      setPracticeIsRecording(false);
    };

    practiceRecognitionRef.current.onend = () => {
      setPracticeIsRecording(false);
    };

    practiceRecognitionRef.current.start();
  };

  const stopPracticeRecording = () => {
    if (practiceRecognitionRef.current) {
      practiceRecognitionRef.current.stop();
    }
    setPracticeIsRecording(false);
  };

  const getLanguageCode = (language) => {
    const langCodes = {
      'English': 'en-US',
      'Hindi': 'hi-IN',
      'Hinglish': 'en-IN',
      'Marathi': 'mr-IN',
      'Kannada': 'kn-IN',
      'Tamil': 'ta-IN',
      'Telugu': 'te-IN',
      'Bangla': 'bn-IN'
    };
    return langCodes[language] || 'en-US';
  };

  const handleObjection = async (objectionText, scenarioId = null) => {
    if (!objectionText || !objectionText.trim()) {
      toast.error('Please provide an objection text');
      return;
    }

    setLoading(true);
    setAiResponse(''); // Clear previous response
    try {
      const response = await axios.post(`${API}/objection/handle`, {
        objection_text: objectionText.trim(),
        language: selectedLanguage,
        scenario_id: scenarioId
      });
      setAiResponse(response.data.response);
      toast.success('AI response generated!');
    } catch (error) {
      toast.error('Failed to get AI response: ' + (error.response?.data?.detail || error.message));
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handlePracticeFeedback = async () => {
    if (!practiceResponse.trim()) {
      toast.error('Please provide a response');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/practice/feedback`, {
        scenario_id: practiceScenarios[currentPracticeIndex].id,
        user_response: practiceResponse,
        response_type: 'text'
      });
      setPracticeFeedback(response.data);
      toast.success('Feedback received!');
    } catch (error) {
      toast.error('Failed to get feedback');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const nextPracticeScenario = () => {
    if (currentPracticeIndex < practiceScenarios.length - 1) {
      setCurrentPracticeIndex(currentPracticeIndex + 1);
      setPracticeResponse('');
      setPracticeFeedback(null);
    } else {
      toast.success('Practice session completed!');
    }
  };

  const HomePage = () => (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <div className="container mx-auto px-6 py-12">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-gray-900 mb-6 bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">
            Sales Training Assistant
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
            Master your sales skills with AI-powered objection handling and practice scenarios. 
            Get real-time assistance for merchant interactions and improve your conversion rates.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          <Card className="group hover:shadow-2xl transition-all duration-300 border-0 bg-white/70 backdrop-blur-sm">
            <CardHeader className="pb-6">
              <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                <MessageCircle className="w-8 h-8 text-white" />
              </div>
              <CardTitle className="text-2xl font-bold text-gray-900">Merchant Check In</CardTitle>
              <CardDescription className="text-gray-600 text-base">
                Get instant AI-powered responses to handle merchant objections in real-time during face-to-face interactions.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3 mb-6 text-gray-600">
                <li className="flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-3"></div>
                  Voice recording support
                </li>
                <li className="flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-3"></div>
                  60+ pre-loaded scenarios
                </li>
                <li className="flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-3"></div>
                  Multi-language support
                </li>
              </ul>
              <Button 
                onClick={() => setCurrentMode('merchant')} 
                className="w-full bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-semibold py-3 rounded-xl transition-all duration-300"
              >
                Start Merchant Check In
              </Button>
            </CardContent>
          </Card>

          <Card className="group hover:shadow-2xl transition-all duration-300 border-0 bg-white/70 backdrop-blur-sm">
            <CardHeader className="pb-6">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                <Target className="w-8 h-8 text-white" />
              </div>
              <CardTitle className="text-2xl font-bold text-gray-900">Practice Mode</CardTitle>
              <CardDescription className="text-gray-600 text-base">
                Practice your sales pitch with 10 random scenarios and get detailed AI feedback to improve your skills.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3 mb-6 text-gray-600">
                <li className="flex items-center">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
                  10 random practice scenarios
                </li>
                <li className="flex items-center">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
                  AI-powered feedback & scoring
                </li>
                <li className="flex items-center">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
                  Detailed improvement suggestions
                </li>
              </ul>
              <Button 
                onClick={() => {
                  setCurrentMode('practice');
                  fetchPracticeScenarios();
                }} 
                className="w-full bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white font-semibold py-3 rounded-xl transition-all duration-300"
              >
                Start Practice Mode
              </Button>
            </CardContent>
          </Card>
        </div>

        <div className="mt-16 text-center">
          <div className="flex justify-center items-center space-x-8 text-gray-500">
            <div className="flex items-center space-x-2">
              <Users className="w-5 h-5" />
              <span>Real-time assistance</span>
            </div>
            <div className="flex items-center space-x-2">
              <MessageCircle className="w-5 h-5" />
              <span>AI-powered responses</span>
            </div>
            <div className="flex items-center space-x-2">
              <Target className="w-5 h-5" />
              <span>Skill improvement</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const MerchantMode = () => (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-emerald-50">
      <div className="container mx-auto px-6 py-8">
        <div className="mb-8">
          <Button 
            onClick={() => setCurrentMode('home')} 
            variant="outline" 
            className="mb-4 hover:bg-green-50"
          >
            ← Back to Home
          </Button>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Merchant Check In</h1>
          <p className="text-gray-600">Handle merchant objections with AI-powered responses</p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          <Card className="bg-white/70 backdrop-blur-sm border-0 shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Mic className="w-5 h-5 text-green-600" />
                <span>Input Objection</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Language</label>
                <Select value={selectedLanguage} onValueChange={setSelectedLanguage}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {languages.map((lang) => (
                      <SelectItem key={lang} value={lang}>{lang}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <Tabs defaultValue="voice" className="w-full">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="voice">Voice Recording</TabsTrigger>
                  <TabsTrigger value="preset">Select Scenario</TabsTrigger>
                </TabsList>
                
                <TabsContent value="voice" className="space-y-4">
                  <div className="text-center">
                    <Button
                      onClick={isRecording ? stopRecording : startRecording}
                      size="lg"
                      className={`w-24 h-24 rounded-full ${
                        isRecording 
                          ? 'bg-red-500 hover:bg-red-600' 
                          : 'bg-green-500 hover:bg-green-600'
                      } text-white transition-all duration-300`}
                    >
                      {isRecording ? <MicOff className="w-8 h-8" /> : <Mic className="w-8 h-8" />}
                    </Button>
                    <p className="mt-2 text-sm text-gray-600">
                      {isRecording ? 'Click to stop recording' : 'Click to start recording'}
                    </p>
                  </div>
                  
                  {recordedText && (
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h4 className="font-medium text-gray-900 mb-2">Recorded Text:</h4>
                      <p className="text-gray-700">{recordedText}</p>
                    </div>
                  )}
                  
                  <Button 
                    onClick={() => handleObjection(recordedText)}
                    disabled={!recordedText.trim() || loading}
                    className="w-full bg-green-600 hover:bg-green-700"
                  >
                    {loading ? <RefreshCw className="w-4 h-4 animate-spin mr-2" /> : null}
                    Get AI Response
                  </Button>
                </TabsContent>
                
                <TabsContent value="preset" className="space-y-4">
                  <Select 
                    value={selectedScenario?.id?.toString() || ''} 
                    onValueChange={(value) => {
                      const scenario = scenarios.find(s => s.id === parseInt(value));
                      setSelectedScenario(scenario);
                      console.log('Selected scenario:', scenario); // Debug log
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select a scenario..." />
                    </SelectTrigger>
                    <SelectContent className="max-h-60">
                      {categories.map((category) => (
                        <div key={category}>
                          <div className="px-2 py-1 text-xs font-medium text-gray-500 bg-gray-100">
                            {category}
                          </div>
                          {scenarios
                            .filter((s) => s.category === category)
                            .map((scenario) => (
                              <SelectItem key={scenario.id} value={scenario.id.toString()}>
                                {scenario.objection}
                              </SelectItem>
                            ))}
                        </div>
                      ))}
                    </SelectContent>
                  </Select>
                  
                  {selectedScenario && (
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <Badge className="mb-2">{selectedScenario.category}</Badge>
                      <h4 className="font-medium text-gray-900 mb-2">Objection:</h4>
                      <p className="text-gray-700 mb-3">{selectedScenario.objection}</p>
                      <h4 className="font-medium text-gray-900 mb-2">Context:</h4>
                      <p className="text-gray-600 text-sm">{selectedScenario.context}</p>
                    </div>
                  )}
                  
                  <Button 
                    onClick={() => {
                      console.log('Button clicked, selectedScenario:', selectedScenario);
                      if (selectedScenario && selectedScenario.objection) {
                        handleObjection(selectedScenario.objection, selectedScenario.id);
                      }
                    }}
                    disabled={!selectedScenario || !selectedScenario.objection || loading}
                    className="w-full bg-green-600 hover:bg-green-700 disabled:opacity-50"
                  >
                    {loading ? <RefreshCw className="w-4 h-4 animate-spin mr-2" /> : null}
                    Get AI Response
                  </Button>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          <Card className="bg-white/70 backdrop-blur-sm border-0 shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Play className="w-5 h-5 text-green-600" />
                <span>AI Response</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {aiResponse ? (
                <div className="bg-green-50 p-6 rounded-lg border-l-4 border-green-500">
                  <h4 className="font-medium text-green-900 mb-3">Suggested Response:</h4>
                  <div className="text-green-800 leading-relaxed prose prose-sm max-w-none">
                    {aiResponse.split('\n').map((line, index) => {
                      // Handle bold text
                      if (line.includes('**')) {
                        const parts = line.split('**');
                        return (
                          <p key={index} className="mb-2">
                            {parts.map((part, partIndex) => 
                              partIndex % 2 === 1 ? 
                                <strong key={partIndex}>{part}</strong> : 
                                part
                            )}
                          </p>
                        );
                      }
                      // Handle bullet points
                      if (line.trim().startsWith('-') || line.trim().startsWith('•')) {
                        return (
                          <li key={index} className="ml-4 mb-1 list-disc">
                            {line.replace(/^[-•]\s*/, '')}
                          </li>
                        );
                      }
                      // Regular paragraphs
                      if (line.trim()) {
                        return <p key={index} className="mb-2">{line}</p>;
                      }
                      return null;
                    })}
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <MessageCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>AI response will appear here after processing your objection</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );

  const PracticeMode = () => (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <div className="container mx-auto px-6 py-8">
        <div className="mb-8">
          <Button 
            onClick={() => setCurrentMode('home')} 
            variant="outline" 
            className="mb-4 hover:bg-blue-50"
          >
            ← Back to Home
          </Button>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Practice Mode</h1>
          <p className="text-gray-600">Practice with random scenarios and get AI feedback</p>
        </div>

        {practiceScenarios.length > 0 && (
          <div className="max-w-4xl mx-auto">
            <div className="mb-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold">
                  Scenario {currentPracticeIndex + 1} of {practiceScenarios.length}
                </h2>
                <Badge variant="outline">
                  {practiceScenarios[currentPracticeIndex]?.category}
                </Badge>
              </div>
              
              <Card className="bg-white/70 backdrop-blur-sm border-0 shadow-lg mb-6">
                <CardContent className="p-6">
                  <h3 className="font-medium text-gray-900 mb-3">Merchant Objection:</h3>
                  <p className="text-lg text-gray-800 mb-4">
                    "{practiceScenarios[currentPracticeIndex]?.objection}"
                  </p>
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <h4 className="font-medium text-blue-900 mb-2">Context:</h4>
                    <p className="text-blue-800 text-sm">
                      {practiceScenarios[currentPracticeIndex]?.context}
                    </p>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-white/70 backdrop-blur-sm border-0 shadow-lg mb-6">
                <CardHeader>
                  <CardTitle>Your Response</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Tabs defaultValue="text" className="w-full">
                    <TabsList className="grid w-full grid-cols-2">
                      <TabsTrigger value="text">Type Response</TabsTrigger>
                      <TabsTrigger value="voice">Voice Recording</TabsTrigger>
                    </TabsList>
                    
                    <TabsContent value="text" className="space-y-4">
                      <Textarea
                        placeholder="How would you respond to this objection? Type your response here..."
                        value={practiceResponse}
                        onChange={(e) => {
                          e.preventDefault();
                          setPracticeResponse(e.target.value);
                        }}
                        onFocus={(e) => e.target.style.outline = 'none'}
                        onBlur={() => {}}
                        rows={6}
                        className="resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        style={{ outline: 'none' }}
                      />
                    </TabsContent>
                    
                    <TabsContent value="voice" className="space-y-4">
                      <div className="text-center">
                        <Button
                          onClick={practiceIsRecording ? stopPracticeRecording : startPracticeRecording}
                          size="lg"
                          className={`w-24 h-24 rounded-full ${
                            practiceIsRecording 
                              ? 'bg-red-500 hover:bg-red-600' 
                              : 'bg-blue-500 hover:bg-blue-600'
                          } text-white transition-all duration-300`}
                        >
                          {practiceIsRecording ? <MicOff className="w-8 h-8" /> : <Mic className="w-8 h-8" />}
                        </Button>
                        <p className="mt-2 text-sm text-gray-600">
                          {practiceIsRecording ? 'Click to stop recording' : 'Click to start recording'}
                        </p>
                      </div>
                      
                      {practiceRecordedText && (
                        <div className="bg-gray-50 p-4 rounded-lg">
                          <h4 className="font-medium text-gray-900 mb-2">Recorded Response:</h4>
                          <p className="text-gray-700">{practiceRecordedText}</p>
                        </div>
                      )}
                    </TabsContent>
                  </Tabs>
                  
                  <Button 
                    onClick={handlePracticeFeedback}
                    disabled={!practiceResponse.trim() || loading}
                    className="w-full bg-blue-600 hover:bg-blue-700"
                  >
                    {loading ? <RefreshCw className="w-4 h-4 animate-spin mr-2" /> : null}
                    Get Feedback
                  </Button>
                </CardContent>
              </Card>

              {practiceFeedback && (
                <Card className="bg-white/70 backdrop-blur-sm border-0 shadow-lg mb-6">
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <span>AI Feedback</span>
                      {practiceFeedback.score && (
                        <Badge className="bg-blue-100 text-blue-800">
                          Score: {practiceFeedback.score}/10
                        </Badge>
                      )}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <h4 className="font-medium text-blue-900 mb-2">Feedback:</h4>
                      <div className="text-blue-800 prose prose-sm max-w-none">
                        {practiceFeedback.feedback.split('\n').map((line, index) => {
                          // Handle bold text
                          if (line.includes('**')) {
                            const parts = line.split('**');
                            return (
                              <p key={index} className="mb-2">
                                {parts.map((part, partIndex) => 
                                  partIndex % 2 === 1 ? 
                                    <strong key={partIndex}>{part}</strong> : 
                                    part
                                )}
                              </p>
                            );
                          }
                          // Handle bullet points
                          if (line.trim().startsWith('-') || line.trim().startsWith('•')) {
                            return (
                              <li key={index} className="ml-4 mb-1 list-disc">
                                {line.replace(/^[-•]\s*/, '')}
                              </li>
                            );
                          }
                          // Regular paragraphs
                          if (line.trim()) {
                            return <p key={index} className="mb-2">{line}</p>;
                          }
                          return null;
                        })}
                      </div>
                    </div>
                    
                    {practiceFeedback.suggestions && practiceFeedback.suggestions.length > 0 && (
                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">Suggestions for Improvement:</h4>
                        <ul className="space-y-2">
                          {practiceFeedback.suggestions.map((suggestion, index) => (
                            <li key={index} className="flex items-start space-x-2">
                              <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                              <span className="text-gray-700">{suggestion}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    <div className="flex space-x-4">
                      <Button
                        onClick={nextPracticeScenario}
                        disabled={currentPracticeIndex >= practiceScenarios.length - 1}
                        className="bg-blue-600 hover:bg-blue-700"
                      >
                        Next Scenario
                      </Button>
                      
                      {currentPracticeIndex >= practiceScenarios.length - 1 && (
                        <Button
                          onClick={() => {
                            fetchPracticeScenarios();
                            setPracticeFeedback(null);
                            setPracticeResponse('');
                            setPracticeRecordedText('');
                          }}
                          variant="outline"
                        >
                          Start New Practice
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen">
      <Toaster position="top-right" />
      
      {currentMode === 'home' && <HomePage />}
      {currentMode === 'merchant' && <MerchantMode />}
      {currentMode === 'practice' && <PracticeMode />}
    </div>
  );
}

export default App;