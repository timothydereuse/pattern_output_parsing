%% SET UP INPUT FILES

coreRoot = "C:\Users\Tim\Documents\code\musicXmlParser\all_pointsets";
outFolder = "C:\Users\Tim\Documents\code\musicXmlParser\patterns_output";

%get list of all text files in tune family database directory
allFilenames = dir(coreRoot);
allFilenames = {allFilenames(3:end).name};

piecePath = "C:\Users\Tim\Documents\code\musicXmlParser\3_op44i_2_corrected.txt"

r = 5;
quick = 0;
compactThresh = 1;
cardinaThresh = 10;
regionType = 'lexicographic';
similarThresh = 0.9;
similarFunc = 'cardinality score';
similarParam = 1;
ratingField = 'cardinality';
inexactThresh = 0.9;

%  r is a positive integer between 1 and n - 1, giving the number of
%   superdiagonals of the similarity array for D that will be used.
%  compactThresh is a parameter in (0, 1], giving the minimum compactness a
%   pattern occurrence must have in order to be included in the output.
%  cardinaThresh is a positive integer parameter, giving the minimum number
%   points that compactness a pattern occurrences must have in order to be
%   included in the output.
%  regionType is a string equal to 'lexicographic' or 'convex hull',
%   indicating which definition of region should be used for calculating
%   the compactness of patterns.
%  quick is an optional logical argument (set to one by default). It will
%   call a quick verison of the function in the default case, but this
%   version is sensitive to even very slight differences between decimal
%   values (look out for tuplets). The slow version is more robust to these
%   differences (down to 5 decimal places).
%  similarThresh is a value in [0, 1). If the similarity of the current
%   highest-rated pattern S_in(i) and some other pattern S_in(j) is greater
%   than this threshold, then S_in(j) will be categorised as an instance of
%   the exemplar S_in(i). Otherwise S_in(j) may become an exemplar in a
%   subsequent step.
%  similarFunc is a string indicating which function should be used for
%   calculating the symbolic music similarity, either 'cardinality score'
%   or 'normalised matching score'.
%  similarParam is an optional argument. If similarFunc = 'cardinality
%   score', then similarParam takes one of two values (one if calculation
%   of cardinality score allows for translations, and zero otherwise). If
%   similarFunc = 'normalised matching score', then similarParam takes a
%   string value ('normal', 'pitchindependent',
%   'tempoindependent', or 'tempoandpitchindependent', see fpgethistogram2
%   for details).
%  ratingField is an optional string indicating which field of each struct
%   in S should be used to order the repeated patterns.

for fileNum = 1:length(allFilenames)

    pieceName = allFilenames{fileNum};
    
    % load piece
    piecePath = fullfile(coreRoot, char(pieceName));
    
    %remove the .musicxml from the end
    pieceName = extractBefore(pieceName,length(pieceName)-9);
    
    % if pieceName(1:9) ~= "3_op44i_3"
    if pieceName(1) ~= "4"
       disp(strcat('Skipping ', pieceName));
       continue 
    end
    disp(strcat('Processing ', pieceName));

    % INPUT
    % D is an n x k matrix representing a k-dimensional set of n points.
    D = lispStylePointSet2Matrix(piecePath,3);
    D = D(:,[1 3]); %keep song ID#, onset time, and MIDI pitch number
    D = sortrows(D);

    %     disp('Running SIAR...');
    %     [SIARoutput, runtime, FRT] = SIAR(D, r, quick);
    % 
    %     disp('Running SIARCT...');
    %     [SIARCToutput, runtime, FRT] = SIARCT(D, r, compactThresh, cardinaThresh,...
    %     regionType,SIARoutput, runtime, FRT, quick);

    disp('Running SIARCT_C...');
    [SCout, prevRuntime, prevFRT] = SIARCT_C(D, r,...
      compactThresh, cardinaThresh, regionType, similarThresh, similarFunc,...
      similarParam, ratingField);
    
%     disp('Running SIARCT_CFP...');
%     [SIARCT_CFPoutput, runtime, FRT] = SIARCT_CFP(D, r,...
%       compactThresh, cardinaThresh, regionType, similarThresh, similarFunc,...
%       similarParam, ratingField, inexactThresh, SCout, 'SIARCT_C',...
%       prevRuntime, prevFRT)

    disp('Exporting to JSON...');
    s = jsonencode(SCout);
    out_fname = fullfile(outFolder, [pieceName '_patterns.json']);
    fid = fopen(out_fname, 'w');
    fwrite(fid, s, 'char');
    fclose(fid);
end