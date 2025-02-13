const API_BASE_URL = '/api';  // This is correct - don't change to port 5000

// Group types
export interface Group {
  id: number;
  name: string;
  words_count: number;
}

export interface GroupsResponse {
  items: Group[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// Word types
export interface WordGroup {
  id: number;
  name: string;
}

export interface Word {
  id: number;
  kanji: string;
  romaji: string;
  english: string;
  correct_count: number;
  wrong_count: number;
  groups: WordGroup[];
}

export interface WordResponse {
  word: Word;
}

export interface WordsResponse {
  words: Word[];
  total_pages: number;
  current_page: number;
  total_words: number;
}

// Study Session types
export interface StudySession {
  id: number;
  group_id: number;
  group_name: string;
  activity_id: number;
  activity_name: string;
  start_time: string;
  end_time: string;
  review_items_count: number;
}

export interface WordReview {
  word_id: number;
  is_correct: boolean;
}

// Dashboard types
export interface RecentSession {
  id: number;
  created_at: string;
  group_name: string;
  activity_name: string;
  words_studied: number;
  success_rate: number;
}

export interface StudyStats {
  total_vocabulary: number;
  total_words_studied: number;
  mastered_words: number;
  success_rate: number;
  total_sessions: number;
  active_groups: number;
  current_streak: number;
}

// Add missing interfaces at the top with other interfaces
export interface GroupDetails {
  id: number;
  group_name: string;
  word_count: number;
}

export interface GroupWordsResponse {
  words: Word[];
  total_pages: number;
  current_page: number;
}

export interface StudySessionsResponse {
  items: StudySession[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export const api = {
  // Words
  getWords: async (page = 1, sortBy = 'kanji', order = 'asc'): Promise<WordsResponse> => {
    const response = await fetch(
      `${API_BASE_URL}/words?page=${page}&sort_by=${sortBy}&order=${order}`,
      {
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      }
    );
    if (!response.ok) throw new Error('Failed to fetch words');
    return response.json();
  },

  getWord: async (id: number): Promise<Word> => {
    const response = await fetch(`${API_BASE_URL}/words/${id}`);
    if (!response.ok) throw new Error('Failed to fetch word details');
    const data: WordResponse = await response.json();
    return data.word;
  },

  searchWords: async (query: string, page = 1) => {
    const response = await fetch(`${API_BASE_URL}/words/search?q=${query}&page=${page}`);
    if (!response.ok) throw new Error('Failed to search words');
    return response.json();
  },

  // Groups
  getGroups: async (
    page: number = 1,
    sortBy: string = 'name',
    order: 'asc' | 'desc' = 'asc'
  ): Promise<GroupsResponse> => {
    const response = await fetch(
      `${API_BASE_URL}/groups?page=${page}&sort_by=${sortBy}&order=${order}`,
      {  // Add headers to prevent caching
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      }
    );
    if (!response.ok) throw new Error('Failed to fetch groups');
    const data = await response.json();
    console.log('Groups API Response:', data);  // Add this log
    return data;
  },

  getGroupDetails: async (groupId: number): Promise<GroupDetails> => {
    const response = await fetch(`${API_BASE_URL}/groups/${groupId}`);
    if (!response.ok) throw new Error('Failed to fetch group details');
    return response.json();
  },

  getGroupWords: async (
    groupId: number,
    page: number = 1,
    sortBy: string = 'kanji',
    order: 'asc' | 'desc' = 'asc'
  ): Promise<GroupWordsResponse> => {
    const response = await fetch(
      `${API_BASE_URL}/groups/${groupId}/words?page=${page}&sort_by=${sortBy}&order=${order}`
    );
    if (!response.ok) throw new Error('Failed to fetch group words');
    return response.json();
  },

  // Study Sessions
  createStudySession: async (
    groupId: number,
    studyActivityId: number
  ): Promise<{ session_id: number }> => {
    const response = await fetch(`${API_BASE_URL}/study-sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ group_id: groupId, study_activity_id: studyActivityId }),
    });
    if (!response.ok) throw new Error('Failed to create study session');
    return response.json();
  },

  getStudySessions: async (
    page: number = 1,
    perPage: number = 10
  ): Promise<StudySessionsResponse> => {
    const response = await fetch(
      `${API_BASE_URL}/study-sessions?page=${page}&per_page=${perPage}`
    );
    if (!response.ok) throw new Error('Failed to fetch study sessions');
    return response.json();
  },

  getGroupStudySessions: async (
    groupId: number,
    page: number = 1,
    sortBy: string = 'created_at',
    order: 'asc' | 'desc' = 'desc'
  ): Promise<StudySessionsResponse> => {
    const response = await fetch(
      `${API_BASE_URL}/groups/${groupId}/study_sessions?page=${page}&sort_by=${sortBy}&order=${order}`
    );
    if (!response.ok) throw new Error('Failed to fetch group study sessions');
    return response.json();
  },

  // Dashboard
  getRecentStudySession: async (): Promise<RecentSession | null> => {
    const response = await fetch(`${API_BASE_URL}/dashboard/recent-session`);
    if (!response.ok) throw new Error('Failed to fetch recent session');
    return response.json();
  },

  getStudyStats: async (): Promise<StudyStats> => {
    const response = await fetch(`${API_BASE_URL}/dashboard/stats`);
    if (!response.ok) throw new Error('Failed to fetch study stats');
    return response.json();
  },

  getStudyActivities: async () => {
    const response = await fetch(`${API_BASE_URL}/study-activities`);
    if (!response.ok) throw new Error('Failed to fetch study activities');
    return response.json();
  },

  // Add missing method for submitting reviews
  submitStudySessionReview: async (
    sessionId: number,
    reviews: WordReview[]
  ): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/study-sessions/${sessionId}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reviews }),
    });
    if (!response.ok) throw new Error('Failed to submit study session review');
  },

  // Remove duplicate methods (fetchRecentStudySession, fetchStudyStats, etc.)
};

// Named exports that map to api methods
export const createStudySession = api.createStudySession;
export const fetchRecentStudySession = api.getRecentStudySession;
export const fetchStudyStats = api.getStudyStats;
export const fetchStudyActivities = api.getStudyActivities;
export const fetchWords = api.getWords;
export const fetchGroups = api.getGroups;
export const fetchWordDetails = api.getWord;
export const fetchGroupDetails = api.getGroupDetails;
export const fetchGroupWords = api.getGroupWords;
export const submitStudySessionReview = api.submitStudySessionReview;
export const fetchGroupStudySessions = api.getGroupStudySessions;
export const fetchStudySessions = api.getStudySessions;

export default api;
